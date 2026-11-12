import json
import os
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import get_db
from app.models import Alert, AnalysisHistory, Product, ProductSource, Report, Review, ReviewAspect, SearchHistory, SourceObservation, User
from app.services.auth import get_current_user
from app.services.analytics.product_intelligence import compute_product_intelligence
from app.services.analytics.review_quality import analyze_review_patterns
from app.services.analytics.sentiment_analytics import (
    compute_rating_distribution,
    compute_summary,
    compute_word_frequency,
)

router = APIRouter(tags=["reports"])


class ReportRequest(BaseModel):
    product_id: int
    report_type: str = "product_summary"


# ─── Alerts ───────────────────────────────────────────────────────────
@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alerts = (
        db.query(Alert)
        .filter(Alert.user_id == current_user.id)
        .order_by(Alert.created_at.desc())
        .limit(100)
        .all()
    )

    return {
        "count": len(alerts),
        "items": [
            {
                "id": a.id,
                "product_id": a.product_id,
                "product_name": a.product.name if a.product else "Unknown",
                "alert_type": a.alert_type,
                "message": a.message,
                "is_read": a.is_read,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
    }


@router.post("/alerts/{alert_id}/read")
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    return {"id": alert.id, "is_read": True}


# ─── Reports ──────────────────────────────────────────────────────────
@router.get("/reports")
def list_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reports = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return {
        "count": len(reports),
        "items": [
            {
                "id": report.id,
                "product_id": report.product_id,
                "product_name": report.product.name if report.product else "Unknown",
                "report_type": report.report_type,
                "file_path": report.file_path,
                "status": "generated" if report.generated_content else "unavailable",
                "created_at": report.created_at.isoformat() if report.created_at else None,
            }
            for report in reports
        ],
    }


@router.get("/reports/{report_id}")
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == current_user.id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    content = {}
    if report.generated_content:
        try:
            content = json.loads(report.generated_content)
        except Exception:
            content = {"raw": report.generated_content}

    return {
        "id": report.id,
        "product_id": report.product_id,
        "product_name": report.product.name if report.product else "Unknown",
        "report_type": report.report_type,
        "file_path": report.file_path,
        "content": content,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.post("/reports")
def create_report(
    payload: ReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")

    reviews = db.query(Review).filter(Review.product_id == product.id).all()
    summary = compute_summary([
        {"sentiment": r.sentiment.sentiment_label if r.sentiment else "neutral", "rating": r.rating}
        for r in reviews
    ])
    rating_dist = compute_rating_distribution(reviews)
    keywords = compute_word_frequency([r.review_text for r in reviews])
    aspect_rows = db.query(ReviewAspect).join(Review).filter(Review.product_id == product.id).all()
    aspects = {}
    for row in aspect_rows:
        entry = aspects.setdefault(row.aspect, {"positive": 0, "neutral": 0, "negative": 0, "scores": []})
        if row.sentiment in {"positive", "neutral", "negative"}:
            entry[row.sentiment] += 1
        entry["scores"].append(row.score)
    aspect_summary = {
        name: {
            "positive": counts["positive"],
            "neutral": counts["neutral"],
            "negative": counts["negative"],
            "average_score": round(sum(counts["scores"]) / len(counts["scores"]), 3) if counts["scores"] else None,
        }
        for name, counts in aspects.items()
    }
    history_rows = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.product_id == product.id)
        .order_by(AnalysisHistory.analyzed_at.asc())
        .all()
    )
    source_records = db.query(ProductSource).filter(ProductSource.product_id == product.id).all()
    source_comparison = []
    price_history = []
    for source in source_records:
        observations = (
            db.query(SourceObservation)
            .filter(SourceObservation.product_source_id == source.id)
            .order_by(SourceObservation.observed_at.asc(), SourceObservation.id.asc())
            .all()
        )
        observation = (
            observations[-1] if observations else None
        )
        source_comparison.append({
            "source": source.source_name,
            "status": observation.data_type if observation else source.data_type,
            "price": float(observation.price) if observation and observation.price is not None else None,
            "rating": observation.rating if observation else None,
            "review_count": observation.review_count if observation else None,
            "availability": observation.availability if observation else None,
            "observed_at": observation.observed_at.isoformat() if observation and observation.observed_at else None,
        })
        price_history.extend({
            "source": source.source_name,
            "price": float(item.price) if item.price is not None else None,
            "currency": item.currency,
            "data_type": item.data_type,
            "observed_at": item.observed_at.isoformat() if item.observed_at else None,
        } for item in observations if item.price is not None)
    provenance = {}
    for review in reviews:
        provenance[review.data_type] = provenance.get(review.data_type, 0) + 1
    intelligence = compute_product_intelligence(
        reviews=reviews,
        average_rating=float(product.average_rating or 0),
        total_reviews=int(product.total_reviews or 0),
        positive_percentage=summary["positive_percentage"],
        neutral_percentage=summary["neutral_percentage"],
        negative_percentage=summary["negative_percentage"],
    )

    # Praises and complaints
    praises = []
    complaints = []
    for review in sorted(reviews, key=lambda r: r.rating or 0, reverse=True):
        if review.sentiment and review.sentiment.sentiment_label == "positive" and len(praises) < 5:
            praises.append(review.review_text[:200])
        elif review.sentiment and review.sentiment.sentiment_label == "negative" and len(complaints) < 5:
            complaints.append(review.review_text[:200])

    report_content = {
        "product_overview": {
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "price": product.price,
            "description": product.description,
        },
        "summary": summary,
        "rating_distribution": rating_dist,
        "aspect_analysis": aspect_summary,
        "source_comparison": source_comparison,
        "price_history": price_history,
        "review_quality": analyze_review_patterns(reviews),
        "top_reviews": [
            {
                "review_id": review.id,
                "rating": review.rating,
                "sentiment": review.sentiment.sentiment_label if review.sentiment else None,
                "review_text": review.review_text[:400],
                "data_type": review.data_type,
            }
            for review in sorted(reviews, key=lambda item: item.rating or 0, reverse=True)[:10]
        ],
        "sentiment_history": [
            {
                "recorded_at": row.analyzed_at.isoformat() if row.analyzed_at else None,
                "positive_percentage": row.positive_percentage,
                "neutral_percentage": row.neutral_percentage,
                "negative_percentage": row.negative_percentage,
                "average_rating": row.average_rating,
                "review_count": row.total_reviews,
            }
            for row in history_rows
        ],
        "data_provenance": provenance,
        "top_keywords": keywords[:15],
        "intelligence": intelligence,
        "customer_praises": praises,
        "customer_complaints": complaints,
    }

    report = Report(
        user_id=current_user.id,
        product_id=product.id,
        report_type=payload.report_type,
        generated_content=json.dumps(report_content),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Try PDF generation
    pdf_path = None
    try:
        pdf_path = _generate_pdf_report(report.id, product, report_content)
        report.file_path = pdf_path
        db.commit()
    except Exception:
        pass  # PDF generation is best-effort

    return {
        "id": report.id,
        "product_id": product.id,
        "product_name": product.name,
        "report_type": payload.report_type,
        "status": "generated",
        "file_path": pdf_path,
        "content": report_content,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.get("/reports/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == current_user.id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not available for download")
    return FileResponse(report.file_path, media_type="application/pdf", filename=f"report_{report_id}.pdf")


@router.get("/exports/{data_type}.csv")
def export_csv(
    data_type: str,
    product_id: int | None = None,
    source: str | None = None,
    sentiment: str | None = None,
    provenance: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data_type not in {"products", "reviews", "sentiments", "aspects", "prices", "comparison", "search_history", "analytics"}:
        raise HTTPException(status_code=400, detail="Unsupported export type.")

    rows = []
    if data_type in {"reviews", "sentiments", "aspects"}:
        query = db.query(Review).join(Product).filter(Review.data_type.in_(["seeded_demo", "live_scraped"]))
        if product_id is not None:
            query = query.filter(Review.product_id == product_id)
        if source:
            query = query.filter(Review.source.ilike(source))
        if sentiment:
            query = query.join(Review.sentiment).filter(Review.sentiment.has(sentiment_label=sentiment.lower()))
        if provenance:
            if provenance not in {"seeded_demo", "live_scraped", "stored", "unverified"}:
                raise HTTPException(status_code=400, detail="Unsupported data provenance.")
            query = query.filter(Review.data_type == provenance)
        if start_date:
            query = query.filter(Review.review_date >= start_date)
        if end_date:
            query = query.filter(Review.review_date <= end_date)
        reviews = query.order_by(Review.review_date.desc()).all()
        if data_type == "reviews":
            rows = [{
                "review_id": review.id,
                "product_id": review.product_id,
                "product_name": review.product.name,
                "rating": review.rating,
                "sentiment": review.sentiment.sentiment_label if review.sentiment else None,
                "review_text": review.review_text,
                "review_date": review.review_date.isoformat() if review.review_date else None,
                "source": review.source,
                "data_type": review.data_type,
                "verified_purchase": review.verified_purchase,
            } for review in reviews]
        elif data_type == "sentiments":
            rows = [{
                "review_id": review.id,
                "product_id": review.product_id,
                "product_name": review.product.name,
                "sentiment": review.sentiment.sentiment_label if review.sentiment else None,
                "polarity": review.sentiment.polarity_score if review.sentiment else None,
                "subjectivity": review.sentiment.subjectivity_score if review.sentiment else None,
                "confidence": review.sentiment.confidence_score if review.sentiment else None,
                "data_type": review.data_type,
            } for review in reviews if review.sentiment]
        else:
            rows = [{
                "review_id": review.id,
                "product_id": review.product_id,
                "product_name": review.product.name,
                "aspect": aspect.aspect,
                "sentiment": aspect.sentiment,
                "score": aspect.score,
                "data_type": review.data_type,
            } for review in reviews for aspect in review.aspects]
    elif data_type in {"prices", "comparison"}:
        query = db.query(SourceObservation, ProductSource, Product).join(
            ProductSource, SourceObservation.product_source_id == ProductSource.id
        ).join(Product, ProductSource.product_id == Product.id)
        if product_id is not None:
            query = query.filter(Product.id == product_id)
        if source:
            query = query.filter(ProductSource.source_name.ilike(source))
        if start_date:
            query = query.filter(SourceObservation.observed_at >= start_date)
        if end_date:
            query = query.filter(SourceObservation.observed_at <= end_date)
        if provenance:
            if provenance not in {"seeded_demo", "live_scraped", "stored"}:
                raise HTTPException(status_code=400, detail="Unsupported data provenance for price exports.")
            query = query.filter(SourceObservation.data_type == provenance)
        observations = query.order_by(SourceObservation.observed_at.desc()).all()
        rows = [{
            "product_id": product.id,
            "product_name": product.name,
            "source": product_source.source_name,
            "price": float(observation.price) if observation.price is not None else None,
            "currency": observation.currency,
            "rating": observation.rating,
            "review_count": observation.review_count,
            "availability": observation.availability,
            "data_type": observation.data_type,
            "observed_at": observation.observed_at.isoformat() if observation.observed_at else None,
        } for observation, product_source, product in observations]
        if sentiment:
            raise HTTPException(status_code=400, detail="Sentiment filter is not applicable to price exports.")
    elif data_type == "search_history":
        query = db.query(SearchHistory).filter(SearchHistory.user_id == current_user.id)
        if product_id is not None:
            query = query.filter(SearchHistory.product_id == product_id)
        if start_date:
            query = query.filter(SearchHistory.searched_at >= start_date)
        if end_date:
            query = query.filter(SearchHistory.searched_at <= end_date)
        rows = [{
            "query": item.query,
            "product_id": item.product_id,
            "platform": item.platform,
            "searched_at": item.searched_at.isoformat() if item.searched_at else None,
        } for item in query.order_by(SearchHistory.searched_at.desc()).all()]
    else:
        query = db.query(Product)
        if product_id is not None:
            query = query.filter(Product.id == product_id)
        products = query.order_by(Product.name.asc()).all()
        for product in products:
            reviews = db.query(Review).filter(Review.product_id == product.id).all()
            summary = compute_summary([{
                "sentiment": review.sentiment.sentiment_label if review.sentiment else "neutral",
                "rating": review.rating,
            } for review in reviews])
            rows.append({
                "product_id": product.id,
                "product_name": product.name,
                "brand": product.brand,
                "category": product.category,
                "average_rating": summary["average_rating"],
                "review_count": summary["total_reviews"],
                "positive_percentage": summary["positive_percentage"],
                "neutral_percentage": summary["neutral_percentage"],
                "negative_percentage": summary["negative_percentage"],
            })

    if not rows:
        raise HTTPException(status_code=404, detail="No database rows match the selected export filters.")
    columns = list(dict.fromkeys(key for row in rows for key in row))
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="reviewlens_{data_type}.csv"'},
    )


def _generate_pdf_report(report_id: int, product, content: dict) -> str:
    """Generate a PDF report using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from xml.sax.saxutils import escape

    reports_dir = os.path.abspath(settings.reports_dir)
    os.makedirs(reports_dir, exist_ok=True)
    filepath = os.path.join(reports_dir, f"report_{report_id}.pdf")

    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, spaceAfter=12)
    heading_style = ParagraphStyle("Heading2b", parent=styles["Heading2"], fontSize=14, spaceAfter=8)
    normal_style = styles["Normal"]

    elements = []
    elements.append(Paragraph("ReviewLens Product Intelligence Report", title_style))
    elements.append(Spacer(1, 6 * mm))

    overview = content.get("product_overview", {})
    elements.append(Paragraph(f"Product: {escape(str(overview.get('name', 'N/A')))}", heading_style))
    elements.append(Paragraph(f"Brand: {escape(str(overview.get('brand', 'N/A')))} | Category: {escape(str(overview.get('category', 'N/A')))} | Catalog price: {escape(str(overview.get('price', 'N/A')))}", normal_style))
    elements.append(Spacer(1, 4 * mm))

    summary = content.get("summary", {})
    summary_data = [
        ["Metric", "Value"],
        ["Total Reviews", str(summary.get("total_reviews", 0))],
        ["Average Rating", str(summary.get("average_rating", 0))],
        ["Positive %", f"{summary.get('positive_percentage', 0)}%"],
        ["Neutral %", f"{summary.get('neutral_percentage', 0)}%"],
        ["Negative %", f"{summary.get('negative_percentage', 0)}%"],
    ]
    t = Table(summary_data, colWidths=[120, 120])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 4 * mm))

    intelligence = content.get("intelligence", {})
    elements.append(Paragraph(f"Intelligence Score: {intelligence.get('intelligence_score', 'N/A')} ({intelligence.get('grade', 'N/A')})", heading_style))
    elements.append(Paragraph(f"Recommendation: {intelligence.get('recommendation', 'N/A')}", normal_style))
    elements.append(Spacer(1, 4 * mm))

    elements.append(Paragraph("Data Provenance", heading_style))
    elements.append(Paragraph(escape(json.dumps(content.get("data_provenance", {}), sort_keys=True)), normal_style))

    aspects = content.get("aspect_analysis", {})
    if aspects:
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph("Aspect Analysis", heading_style))
        aspect_rows = [["Aspect", "Positive", "Neutral", "Negative", "Mean score"]]
        aspect_rows.extend([
            [escape(str(name)), str(data["positive"]), str(data["neutral"]), str(data["negative"]), str(data.get("average_score") or "N/A")]
            for name, data in list(aspects.items())[:12]
        ])
        aspect_table = Table(aspect_rows, repeatRows=1)
        aspect_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]))
        elements.append(aspect_table)

    sources = content.get("source_comparison", [])
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph("Source Observations", heading_style))
    if sources:
        source_rows = [["Source", "Status", "Price", "Rating", "Reviews", "Observed"]]
        source_rows.extend([
            [escape(str(item.get("source"))), escape(str(item.get("status"))), str(item.get("price") or "Unavailable"), str(item.get("rating") or "Unavailable"), str(item.get("review_count") or "Unavailable"), escape(str(item.get("observed_at") or "Unavailable"))]
            for item in sources[:12]
        ])
        source_table = Table(source_rows, repeatRows=1)
        source_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), 8)]))
        elements.append(source_table)
    else:
        elements.append(Paragraph("No source observations are stored. Live data was not verified.", normal_style))

    price_history = content.get("price_history", [])
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph("Price History", heading_style))
    if price_history:
        for point in price_history[-20:]:
            elements.append(Paragraph(escape(f"{point.get('observed_at')}: {point.get('source')} {point.get('currency') or ''} {point.get('price')} [{point.get('data_type')}]."), normal_style))
    else:
        elements.append(Paragraph("Insufficient historical price data.", normal_style))

    quality = content.get("review_quality", {})
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph("Review Quality Signals", heading_style))
    elements.append(Paragraph(escape(str(quality.get("summary", "Insufficient review data."))), normal_style))
    for signal in quality.get("signals", []):
        elements.append(Paragraph(escape(f"{signal.get('level')}: {signal.get('message')}"), normal_style))

    praises = content.get("customer_praises", [])
    if praises:
        elements.append(Paragraph("Customer Praises", heading_style))
        for p in praises[:3]:
            elements.append(Paragraph(escape(f"- {p}"), normal_style))
        elements.append(Spacer(1, 3 * mm))

    complaints = content.get("customer_complaints", [])
    if complaints:
        elements.append(Paragraph("Customer Complaints", heading_style))
        for c in complaints[:3]:
            elements.append(Paragraph(escape(f"- {c}"), normal_style))

    top_reviews = content.get("top_reviews", [])
    if top_reviews:
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph("Representative Reviews", heading_style))
        for review in top_reviews[:5]:
            elements.append(Paragraph(escape(f"{review.get('rating')}/5 · {review.get('sentiment') or 'unscored'} · {review.get('data_type')}: {review.get('review_text')}"), normal_style))

    doc.build(elements)
    return filepath
