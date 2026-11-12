from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.database import Base
from app.models import Product, ProductSource, Review, ReviewAspect, SentimentResult, SourceObservation
from app.services.demo_catalog import build_additional_products
from app.services.sentiment_service import SentimentAnalyzerService
from app.sources.catalog import SUPPORTED_SOURCES

DB_PATH = Path(__file__).resolve().parent / "product_sentiment.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

PRODUCT_CATALOG = [
    {"name": "iPhone 15", "brand": "Apple", "category": "Smartphones", "subcategory": "Premium Phones", "source": "seed", "product_url": "https://example.com/iphone-15", "image_url": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=900&q=80", "description": "A flagship smartphone with strong camera quality and excellent ecosystem integration.", "features": "Camera;Display;Performance;Battery;Software", "price": "₹79,900"},
    {"name": "iPhone 15 Pro", "brand": "Apple", "category": "Smartphones", "subcategory": "Premium Phones", "source": "seed", "product_url": "https://example.com/iphone-15-pro", "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=80", "description": "Titanium design paired with exceptional camera and premium display performance.", "features": "Camera;Display;Build Quality;Performance;Price", "price": "₹1,34,900"},
    {"name": "iPhone 16", "brand": "Apple", "category": "Smartphones", "subcategory": "Premium Phones", "source": "seed", "product_url": "https://example.com/iphone-16", "image_url": "https://images.unsplash.com/photo-1671725779141-92b17be35d48?auto=format&fit=crop&w=900&q=80", "description": "Apple’s newest flagship focused on camera improvements, performance, and battery efficiency.", "features": "Camera;Battery;Display;Performance;Software", "price": "₹89,900"},
    {"name": "Samsung Galaxy S23", "brand": "Samsung", "category": "Smartphones", "subcategory": "Flagship Phones", "source": "seed", "product_url": "https://example.com/samsung-galaxy-s23", "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&w=900&q=80", "description": "Balanced flagship with power efficiency, strong camera performance, and vibrant display.", "features": "Camera;Display;Battery;Performance;Software", "price": "₹64,999"},
    {"name": "Samsung Galaxy S24", "brand": "Samsung", "category": "Smartphones", "subcategory": "Flagship Phones", "source": "seed", "product_url": "https://example.com/samsung-galaxy-s24", "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90?auto=format&fit=crop&w=900&q=80", "description": "AI-assisted imaging and a refined premium experience with excellent brightness.", "features": "Camera;Display;Software;Features;Battery", "price": "₹69,999"},
    {"name": "Samsung Galaxy S25", "brand": "Samsung", "category": "Smartphones", "subcategory": "Flagship Phones", "source": "seed", "product_url": "https://example.com/samsung-galaxy-s25", "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80", "description": "Premium design, AI performance, and dependable flagship-class battery life.", "features": "Performance;Camera;Battery;Display;Build Quality", "price": "₹74,999"},
    {"name": "OnePlus 12", "brand": "OnePlus", "category": "Smartphones", "subcategory": "Performance Phones", "source": "seed", "product_url": "https://example.com/oneplus-12", "image_url": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=80", "description": "Known for fast charging, excellent performance, and a sleek high-refresh display.", "features": "Performance;Charging;Display;Battery;Software", "price": "₹59,999"},
    {"name": "OnePlus 13", "brand": "OnePlus", "category": "Smartphones", "subcategory": "Performance Phones", "source": "seed", "product_url": "https://example.com/oneplus-13", "image_url": "https://images.unsplash.com/photo-1556656793-08538906a9f8?auto=format&fit=crop&w=900&q=80", "description": "High-end performance and charging speed with a smooth display experience.", "features": "Performance;Display;Charging;Battery;Software", "price": "₹64,999"},
    {"name": "Google Pixel 8", "brand": "Google", "category": "Smartphones", "subcategory": "Camera Phones", "source": "seed", "product_url": "https://example.com/google-pixel-8", "image_url": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?auto=format&fit=crop&w=900&q=80", "description": "Great camera processing, clean software, and strong photography-focused user experience.", "features": "Camera;Software;Battery;Display;Performance", "price": "₹59,999"},
    {"name": "Google Pixel 9", "brand": "Google", "category": "Smartphones", "subcategory": "Camera Phones", "source": "seed", "product_url": "https://example.com/google-pixel-9", "image_url": "https://images.unsplash.com/photo-1601784551446-20c9e07edd80?auto=format&fit=crop&w=900&q=80", "description": "A refined Google flagship with advanced photography and thoughtful software polish.", "features": "Camera;Software;Performance;Battery;Features", "price": "₹69,999"},
    {"name": "Redmi Note 13", "brand": "Xiaomi", "category": "Smartphones", "subcategory": "Value Phones", "source": "seed", "product_url": "https://example.com/redmi-note-13", "image_url": "https://images.unsplash.com/photo-1580910051074-3eb694886505?auto=format&fit=crop&w=900&q=80", "description": "Excellent value for money with a bright display and long battery life.", "features": "Battery;Display;Price;Performance;Camera", "price": "₹18,999"},
    {"name": "Redmi Note 14", "brand": "Xiaomi", "category": "Smartphones", "subcategory": "Value Phones", "source": "seed", "product_url": "https://example.com/redmi-note-14", "image_url": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?auto=format&fit=crop&w=900&q=80", "description": "Strong battery endurance and impressive price-to-performance for everyday use.", "features": "Price;Battery;Display;Performance;Camera", "price": "₹19,999"},
    {"name": "Nothing Phone 2", "brand": "Nothing", "category": "Smartphones", "subcategory": "Design Phones", "source": "seed", "product_url": "https://example.com/nothing-phone-2", "image_url": "https://images.unsplash.com/photo-1598327105740-3c9d7a6f5f9a?auto=format&fit=crop&w=900&q=80", "description": "Distinctive design with clean software and dependable everyday performance.", "features": "Design;Software;Display;Performance;Battery", "price": "₹34,999"},
    {"name": "Nothing Phone 3", "brand": "Nothing", "category": "Smartphones", "subcategory": "Design Phones", "source": "seed", "product_url": "https://example.com/nothing-phone-3", "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=80", "description": "Ethically designed phone with a bold look and streamlined user interface.", "features": "Design;Software;Display;Features;Battery", "price": "₹39,999"},
    {"name": "Realme GT", "brand": "Realme", "category": "Smartphones", "subcategory": "Performance Phones", "source": "seed", "product_url": "https://example.com/realme-gt", "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80", "description": "Performance-focused device with a stylish display and strong value for enthusiasts.", "features": "Performance;Display;Price;Battery;Camera", "price": "₹26,999"},
    {"name": "Vivo V30", "brand": "Vivo", "category": "Smartphones", "subcategory": "Camera Phones", "source": "seed", "product_url": "https://example.com/vivo-v30", "image_url": "https://images.unsplash.com/photo-1571781926291-c477ebfd024b?auto=format&fit=crop&w=900&q=80", "description": "Strong front-camera focus with pleasing design and balanced everyday performance.", "features": "Camera;Design;Battery;Performance;Features", "price": "₹31,999"},
    {"name": "Oppo Reno", "brand": "OPPO", "category": "Smartphones", "subcategory": "Camera Phones", "source": "seed", "product_url": "https://example.com/oppo-reno", "image_url": "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=900&q=80", "description": "Camera leaning mid-range model with a polished display and vibrant styling.", "features": "Camera;Display;Price;Design;Battery", "price": "₹27,999"},
    {"name": "Motorola Edge", "brand": "Motorola", "category": "Smartphones", "subcategory": "Slim Phones", "source": "seed", "product_url": "https://example.com/motorola-edge", "image_url": "https://images.unsplash.com/photo-1525598912003-663126343e1f?auto=format&fit=crop&w=900&q=80", "description": "Thin, sleek, and stylish, with smooth everyday performance and dependable battery life.", "features": "Design;Display;Performance;Battery;Price", "price": "₹27,999"},
    {"name": "MacBook Air M2", "brand": "Apple", "category": "Laptops", "subcategory": "Ultrabooks", "source": "seed", "product_url": "https://example.com/macbook-air-m2", "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80", "description": "Ultra-light premium laptop with excellent battery life and a beautiful display.", "features": "Battery;Display;Performance;Build Quality;Portability", "price": "₹1,09,900"},
    {"name": "MacBook Air M3", "brand": "Apple", "category": "Laptops", "subcategory": "Ultrabooks", "source": "seed", "product_url": "https://example.com/macbook-air-m3", "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80", "description": "Apple’s lightweight performance laptop with efficient performance and silent operation.", "features": "Performance;Battery;Display;Build Quality;Portability", "price": "₹1,19,900"},
    {"name": "MacBook Pro", "brand": "Apple", "category": "Laptops", "subcategory": "Workstations", "source": "seed", "product_url": "https://example.com/macbook-pro", "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80", "description": "Prosumer laptop with premium design, strong performance, and excellent display quality.", "features": "Performance;Display;Battery;Build Quality;Features", "price": "₹1,79,900"},
    {"name": "Dell Inspiron", "brand": "Dell", "category": "Laptops", "subcategory": "Everyday Laptops", "source": "seed", "product_url": "https://example.com/dell-inspiron", "image_url": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=900&q=80", "description": "Balanced productivity laptop with reasonable performance for students and home users.", "features": "Price;Performance;Battery;Features;Build Quality", "price": "₹52,999"},
    {"name": "Dell XPS", "brand": "Dell", "category": "Laptops", "subcategory": "Premium Laptops", "source": "seed", "product_url": "https://example.com/dell-xps", "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80", "description": "Premium ultrabook with great design, high brightness, and dependable performance.", "features": "Display;Build Quality;Performance;Battery;Portability", "price": "₹95,999"},
    {"name": "HP Pavilion", "brand": "HP", "category": "Laptops", "subcategory": "Everyday Laptops", "source": "seed", "product_url": "https://example.com/hp-pavilion", "image_url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=900&q=80", "description": "A practical laptop for students and casual creators who need everyday reliability.", "features": "Price;Performance;Battery;Display;Features", "price": "₹49,999"},
    {"name": "HP Victus", "brand": "HP", "category": "Laptops", "subcategory": "Gaming Laptops", "source": "seed", "product_url": "https://example.com/hp-victus", "image_url": "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?auto=format&fit=crop&w=900&q=80", "description": "Gaming-friendly laptop with strong mid-range graphics and robust cooling.", "features": "Performance;Display;Cooling;Features;Price", "price": "₹68,999"},
    {"name": "HP Envy", "brand": "HP", "category": "Laptops", "subcategory": "Premium Laptops", "source": "seed", "product_url": "https://example.com/hp-envy", "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80", "description": "Stylish and capable premium laptop for creators and productivity-focused users.", "features": "Performance;Display;Build Quality;Battery;Features", "price": "₹89,999"},
    {"name": "Lenovo IdeaPad", "brand": "Lenovo", "category": "Laptops", "subcategory": "Everyday Laptops", "source": "seed", "product_url": "https://example.com/lenovo-ideapad", "image_url": "https://images.unsplash.com/photo-1550236520-7050f3582da0?auto=format&fit=crop&w=900&q=80", "description": "Reliable and affordable laptop designed for day-to-day usage and productivity.", "features": "Price;Battery;Performance;Build Quality;Display", "price": "₹42,999"},
    {"name": "Lenovo ThinkPad", "brand": "Lenovo", "category": "Laptops", "subcategory": "Business Laptops", "source": "seed", "product_url": "https://example.com/lenovo-thinkpad", "image_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80", "description": "Business-class durability, keyboard comfort, and dependable performance.", "features": "Build Quality;Comfort;Performance;Battery;Features", "price": "₹79,999"},
    {"name": "Lenovo Legion", "brand": "Lenovo", "category": "Laptops", "subcategory": "Gaming Laptops", "source": "seed", "product_url": "https://example.com/lenovo-legion", "image_url": "https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=900&q=80", "description": "Gaming-focused machine with strong thermal management and high refresh rates.", "features": "Performance;Cooling;Display;Features;Battery", "price": "₹86,999"},
    {"name": "ASUS Vivobook", "brand": "ASUS", "category": "Laptops", "subcategory": "Everyday Laptops", "source": "seed", "product_url": "https://example.com/asus-vivobook", "image_url": "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?auto=format&fit=crop&w=900&q=80", "description": "Versatile laptop with a comfortable keyboard and useful performance for regular workloads.", "features": "Comfort;Battery;Performance;Price;Display", "price": "₹54,999"},
    {"name": "ASUS TUF", "brand": "ASUS", "category": "Laptops", "subcategory": "Gaming Laptops", "source": "seed", "product_url": "https://example.com/asus-tuf", "image_url": "https://images.unsplash.com/photo-1576602976047-174e57a4784d?auto=format&fit=crop&w=900&q=80", "description": "Value-oriented gaming laptop built for better thermal durability and solid framerates.", "features": "Performance;Build Quality;Display;Cooling;Price", "price": "₹72,999"},
    {"name": "ASUS ROG", "brand": "ASUS", "category": "Laptops", "subcategory": "Gaming Laptops", "source": "seed", "product_url": "https://example.com/asus-rog", "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?auto=format&fit=crop&w=900&q=80", "description": "High-end gaming performance with premium displays and enthusiast-oriented features.", "features": "Performance;Display;Cooling;Features;Build Quality", "price": "₹1,19,999"},
    {"name": "Acer Aspire", "brand": "Acer", "category": "Laptops", "subcategory": "Everyday Laptops", "source": "seed", "product_url": "https://example.com/acer-aspire", "image_url": "https://images.unsplash.com/photo-1587723958656-7f8d4d0f3d3b?auto=format&fit=crop&w=900&q=80", "description": "Affordable laptop with a clean display and practical everyday usability.", "features": "Price;Display;Battery;Performance;Software", "price": "₹39,999"},
    {"name": "Acer Nitro", "brand": "Acer", "category": "Laptops", "subcategory": "Gaming Laptops", "source": "seed", "product_url": "https://example.com/acer-nitro", "image_url": "https://images.unsplash.com/photo-1602080858428-57174f9431cf?auto=format&fit=crop&w=900&q=80", "description": "Affordable gaming performance with a bright display and strong value proposition.", "features": "Performance;Display;Price;Cooling;Battery", "price": "₹67,999"},
    # Tablets
    {"name": "iPad Pro M4", "brand": "Apple", "category": "Tablets", "subcategory": "Pro Tablets", "source": "seed", "product_url": "https://example.com/ipad-pro", "image_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=900&q=80", "description": "Ultra-thin tablet with OLED display and desktop-grade M4 processor performance.", "features": "Display;Performance;Battery;Build Quality;Design", "price": "₹99,900"},
    {"name": "iPad Air M2", "brand": "Apple", "category": "Tablets", "subcategory": "Consumer Tablets", "source": "seed", "product_url": "https://example.com/ipad-air", "image_url": "https://images.unsplash.com/photo-1561154464-82e9adf32764?auto=format&fit=crop&w=900&q=80", "description": "Lightweight, versatile tablet perfect for creativity, note-taking, and entertainment.", "features": "Performance;Display;Comfort;Battery;Software", "price": "₹59,900"},
    {"name": "Samsung Galaxy Tab S9", "brand": "Samsung", "category": "Tablets", "subcategory": "Android Tablets", "source": "seed", "product_url": "https://example.com/galaxy-tab-s9", "image_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=900&q=80", "description": "Vibrant AMOLED screen with bundled S-Pen, water resistance, and desktop mode.", "features": "Display;Performance;Durability;Battery;Software", "price": "₹67,999"},
    {"name": "OnePlus Pad 2", "brand": "OnePlus", "category": "Tablets", "subcategory": "Android Tablets", "source": "seed", "product_url": "https://example.com/oneplus-pad-2", "image_url": "https://images.unsplash.com/photo-1561154464-82e9adf32764?auto=format&fit=crop&w=900&q=80", "description": "High refresh rate tablet with fast charging and productivity-ready aspect ratio.", "features": "Display;Charging;Performance;Sound;Battery", "price": "₹39,999"},
    {"name": "Lenovo Tab P12", "brand": "Lenovo", "category": "Tablets", "subcategory": "Budget Tablets", "source": "seed", "product_url": "https://example.com/lenovo-tab-p12", "image_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=900&q=80", "description": "Large screen tablet designed for media consumption, study, and reading.", "features": "Display;Sound;Price;Battery;Comfort", "price": "₹24,999"},

    # Earbuds
    {"name": "Apple AirPods", "brand": "Apple", "category": "Earbuds", "subcategory": "Wireless Earbuds", "source": "seed", "product_url": "https://example.com/apple-airpods", "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80", "description": "Convenient earbuds with balanced audio and seamless device pairing.", "features": "Sound;Comfort;Battery;Features;Price", "price": "₹14,999"},
    {"name": "AirPods Pro", "brand": "Apple", "category": "Earbuds", "subcategory": "Wireless Earbuds", "source": "seed", "product_url": "https://example.com/airpods-pro", "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80", "description": "Premium in-ear audio with active noise cancellation and comfortable fit.", "features": "Sound;Comfort;Noise Cancellation;Battery;Features", "price": "₹24,999"},
    {"name": "JBL Tune", "brand": "JBL", "category": "Earbuds", "subcategory": "Wireless Earbuds", "source": "seed", "product_url": "https://example.com/jbl-tune", "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80", "description": "Bass-forward audio with a comfortable, budget-friendly wearing experience.", "features": "Sound;Price;Comfort;Battery;Features", "price": "₹4,499"},
    {"name": "boAt Airdopes", "brand": "boAt", "category": "Earbuds", "subcategory": "Wireless Earbuds", "source": "seed", "product_url": "https://example.com/boat-airdopes", "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90?auto=format&fit=crop&w=900&q=80", "description": "Budget-friendly earbuds with stable connectivity and useful battery performance.", "features": "Price;Sound;Battery;Comfort;Features", "price": "₹2,499"},
    {"name": "Noise Buds", "brand": "Noise", "category": "Earbuds", "subcategory": "Wireless Earbuds", "source": "seed", "product_url": "https://example.com/noise-buds", "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80", "description": "Trendy earbuds with good battery and decent audio quality for casual users.", "features": "Battery;Sound;Price;Comfort;Features", "price": "₹2,999"},
    {"name": "OnePlus Buds", "brand": "OnePlus", "category": "Earbuds", "subcategory": "Wireless Earbuds", "source": "seed", "product_url": "https://example.com/oneplus-buds", "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80", "description": "Clear, clean audio with good comfort and reliable everyday performance.", "features": "Sound;Comfort;Battery;Performance;Price", "price": "₹4,999"},
    {"name": "Samsung Galaxy Buds", "brand": "Samsung", "category": "Earbuds", "subcategory": "Wireless Earbuds", "source": "seed", "product_url": "https://example.com/samsung-galaxy-buds", "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80", "description": "Reliable earbuds with strong pairing and balanced sound for everyday listening.", "features": "Sound;Comfort;Battery;Software;Features", "price": "₹7,990"},
    {"name": "Nothing Ear", "brand": "Nothing", "category": "Earbuds", "subcategory": "Wireless Earbuds", "source": "seed", "product_url": "https://example.com/nothing-ear", "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90?auto=format&fit=crop&w=900&q=80", "description": "Clean wireless audio with a distinct design and comfortable fit.", "features": "Sound;Design;Comfort;Battery;Features", "price": "₹5,999"},

    # Headphones
    {"name": "Sony WH-1000XM5", "brand": "Sony", "category": "Headphones", "subcategory": "Noise Cancelling Headphones", "source": "seed", "product_url": "https://example.com/sony-wh-1000xm5", "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80", "description": "Premium noise cancelling headphones loved for wide soundstage and comfort.", "features": "Sound;Comfort;Battery;Features;Noise Cancellation", "price": "₹29,990"},
    {"name": "Sony WH-1000XM6", "brand": "Sony", "category": "Headphones", "subcategory": "Noise Cancelling Headphones", "source": "seed", "product_url": "https://example.com/sony-wh-1000xm6", "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80", "description": "Expected flagship over-ear audio with excellent noise control and immersive sound.", "features": "Sound;Comfort;Noise Cancellation;Battery;Performance", "price": "₹34,990"},
    {"name": "boAt Rockerz", "brand": "boAt", "category": "Headphones", "subcategory": "Wireless Headphones", "source": "seed", "product_url": "https://example.com/boat-rockerz", "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90?auto=format&fit=crop&w=900&q=80", "description": "Affordable wireless headphones with punchy bass and long battery life.", "features": "Sound;Price;Battery;Comfort;Features", "price": "₹1,999"},
    {"name": "JBL Live", "brand": "JBL", "category": "Headphones", "subcategory": "Wireless Headphones", "source": "seed", "product_url": "https://example.com/jbl-live", "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80", "description": "Balanced tuning with an energetic sound signature and sturdy connection quality.", "features": "Sound;Battery;Performance;Comfort;Features", "price": "₹8,999"},
    {"name": "Bose QuietComfort 45", "brand": "Bose", "category": "Headphones", "subcategory": "Noise Cancelling Headphones", "source": "seed", "product_url": "https://example.com/bose-qc45", "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80", "description": "Legendary noise cancellation with plush earcups and world-class sound clarity.", "features": "Sound;Comfort;Noise Cancellation;Durability;Battery", "price": "₹28,990"},

    # Smartwatches
    {"name": "Apple Watch", "brand": "Apple", "category": "Smartwatches", "subcategory": "Premium Smartwatches", "source": "seed", "product_url": "https://example.com/apple-watch", "image_url": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=80", "description": "Well-integrated smartwatch with health features and premium build quality.", "features": "Features;Battery;Comfort;Design;Software", "price": "₹39,900"},
    {"name": "Samsung Galaxy Watch", "brand": "Samsung", "category": "Smartwatches", "subcategory": "Premium Smartwatches", "source": "seed", "product_url": "https://example.com/samsung-galaxy-watch", "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80", "description": "Comprehensive wellness tracking and smart features in a stylish wearable form.", "features": "Features;Battery;Display;Comfort;Software", "price": "₹27,999"},
    {"name": "Noise ColorFit", "brand": "Noise", "category": "Smartwatches", "subcategory": "Budget Smartwatches", "source": "seed", "product_url": "https://example.com/noise-colorfit", "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80", "description": "Affordable smartwatch with a useful feature set and good battery value.", "features": "Price;Battery;Features;Comfort;Display", "price": "₹2,499"},
    {"name": "boAt Wave", "brand": "boAt", "category": "Smartwatches", "subcategory": "Budget Smartwatches", "source": "seed", "product_url": "https://example.com/boat-wave", "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80", "description": "Budget-friendly smartwatch with a sporty design and decent tracking features.", "features": "Price;Features;Battery;Comfort;Design", "price": "₹2,199"},
    {"name": "Fire-Boltt Ninja", "brand": "Fire-Boltt", "category": "Smartwatches", "subcategory": "Budget Smartwatches", "source": "seed", "product_url": "https://example.com/fire-boltt-ninja", "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80", "description": "Value-packed smartwatch with everyday fitness and notification support.", "features": "Price;Features;Battery;Comfort;Display", "price": "₹1,999"},
    {"name": "Amazfit GTR", "brand": "Amazfit", "category": "Smartwatches", "subcategory": "Fitness Watches", "source": "seed", "product_url": "https://example.com/amazfit-gtr", "image_url": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=80", "description": "Fitness-oriented watch with strong battery and broad health tracking capabilities.", "features": "Battery;Features;Comfort;Display;Fitness", "price": "₹8,499"},
    {"name": "Amazfit Bip", "brand": "Amazfit", "category": "Smartwatches", "subcategory": "Fitness Watches", "source": "seed", "product_url": "https://example.com/amazfit-bip", "image_url": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=80", "description": "Affordable fitness tracker with strong battery life and easy daily usability.", "features": "Battery;Features;Price;Comfort;Fitness", "price": "₹4,499"},

    # Cameras
    {"name": "Canon EOS", "brand": "Canon", "category": "Cameras", "subcategory": "DSLRs", "source": "seed", "product_url": "https://example.com/canon-eos", "image_url": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=900&q=80", "description": "Reliable DSLR system with strong image quality and fast autofocus performance.", "features": "Camera;Performance;Build Quality;Features;Price", "price": "₹49,999"},
    {"name": "Nikon Z Series", "brand": "Nikon", "category": "Cameras", "subcategory": "Mirrorless", "source": "seed", "product_url": "https://example.com/nikon-z-series", "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80", "description": "Mirrorless options loved for rich detail, sharp autofocus, and flexible lens ecosystem.", "features": "Camera;Performance;Features;Build Quality;Software", "price": "₹59,999"},
    {"name": "Sony Alpha", "brand": "Sony", "category": "Cameras", "subcategory": "Mirrorless", "source": "seed", "product_url": "https://example.com/sony-alpha", "image_url": "https://images.unsplash.com/photo-1564466809058-bf4114d55352?auto=format&fit=crop&w=900&q=80", "description": "Excellent autofocus and image quality, especially for action and travel photography.", "features": "Camera;Performance;Features;Software;Build Quality", "price": "₹69,999"},
    {"name": "Fujifilm X Series", "brand": "Fujifilm", "category": "Cameras", "subcategory": "Mirrorless", "source": "seed", "product_url": "https://example.com/fujifilm-x-series", "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80", "description": "Strong image colors and a premium design that appeals to creative photographers.", "features": "Camera;Design;Features;Build Quality;Performance", "price": "₹62,999"},
    {"name": "GoPro Hero", "brand": "GoPro", "category": "Cameras", "subcategory": "Action Cameras", "source": "seed", "product_url": "https://example.com/gopro-hero", "image_url": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=900&q=80", "description": "Popular action camera with strong stabilization and reliable outdoor shooting.", "features": "Camera;Durability;Features;Performance;Price", "price": "₹28,999"},
    {"name": "DJI Osmo", "brand": "DJI", "category": "Cameras", "subcategory": "Action Cameras", "source": "seed", "product_url": "https://example.com/dji-osmo", "image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80", "description": "Versatile camera stabilizer with smooth motion and reliable video quality.", "features": "Camera;Features;Performance;Build Quality;Price", "price": "₹33,999"},

    # TVs
    {"name": "Samsung Smart TV", "brand": "Samsung", "category": "TVs", "subcategory": "Smart TVs", "source": "seed", "product_url": "https://example.com/samsung-smart-tv", "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=900&q=80", "description": "Good image quality and intuitive smart features for a modern viewing setup.", "features": "Display;Performance;Features;Software;Price", "price": "₹54,999"},
    {"name": "LG OLED", "brand": "LG", "category": "TVs", "subcategory": "OLED TVs", "source": "seed", "product_url": "https://example.com/lg-oled", "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=900&q=80", "description": "High-contrast OLED image quality with vivid colors and immersive viewing experience.", "features": "Display;Performance;Build Quality;Features;Price", "price": "₹79,999"},
    {"name": "Sony Bravia", "brand": "Sony", "category": "TVs", "subcategory": "Smart TVs", "source": "seed", "product_url": "https://example.com/sony-bravia", "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=900&q=80", "description": "Strong picture processing, premium tuning, and a polished user interface.", "features": "Display;Software;Performance;Features;Build Quality", "price": "₹72,999"},
    {"name": "OnePlus TV", "brand": "OnePlus", "category": "TVs", "subcategory": "Smart TVs", "source": "seed", "product_url": "https://example.com/oneplus-tv", "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=900&q=80", "description": "Competitive large-screen TV with good value and smooth Android-based streaming.", "features": "Display;Price;Software;Features;Performance", "price": "₹48,999"},
    {"name": "Xiaomi Smart TV", "brand": "Xiaomi", "category": "TVs", "subcategory": "Budget TVs", "source": "seed", "product_url": "https://example.com/xiaomi-smart-tv", "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=900&q=80", "description": "Budget-friendly TV with decent image output and a large-screen viewing experience.", "features": "Price;Display;Features;Performance;Software", "price": "₹35,999"},
    {"name": "TCL Smart TV", "brand": "TCL", "category": "TVs", "subcategory": "Budget TVs", "source": "seed", "product_url": "https://example.com/tcl-smart-tv", "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=900&q=80", "description": "Solid value for size and streaming, with a good all-round experience for households.", "features": "Price;Display;Features;Software;Performance", "price": "₹32,999"},

    # Home Appliances
    {"name": "LG Washing Machine", "brand": "LG", "category": "Home Appliances", "subcategory": "Laundry", "source": "seed", "product_url": "https://example.com/lg-washing-machine", "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80", "description": "Reliable washing performance with useful smart wash cycles and quiet operation.", "features": "Performance;Features;Durability;Noise;Price", "price": "₹38,999"},
    {"name": "Samsung Washing Machine", "brand": "Samsung", "category": "Home Appliances", "subcategory": "Laundry", "source": "seed", "product_url": "https://example.com/samsung-washing-machine", "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80", "description": "Strong wash quality and flexible settings for a wide range of laundry needs.", "features": "Performance;Features;Durability;Efficiency;Price", "price": "₹42,999"},
    {"name": "Whirlpool Washing Machine", "brand": "Whirlpool", "category": "Home Appliances", "subcategory": "Laundry", "source": "seed", "product_url": "https://example.com/whirlpool-washing-machine", "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80", "description": "Dependable and practical appliance with straightforward controls and good cleaning action.", "features": "Performance;Price;Durability;Features;Ease of Use", "price": "₹35,999"},
    {"name": "IFB Washing Machine", "brand": "IFB", "category": "Home Appliances", "subcategory": "Laundry", "source": "seed", "product_url": "https://example.com/ifb-washing-machine", "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80", "description": "Smooth cleaning experience with practical programs and reliable operation.", "features": "Performance;Features;Durability;Price;Noise", "price": "₹40,999"},
    {"name": "LG Refrigerator", "brand": "LG", "category": "Home Appliances", "subcategory": "Cooling", "source": "seed", "product_url": "https://example.com/lg-refrigerator", "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80", "description": "Energy-efficient cooling and smart layout features for daily household use.", "features": "Cooling;Durability;Capacity;Features;Efficiency", "price": "₹58,999"},
    {"name": "Samsung Refrigerator", "brand": "Samsung", "category": "Home Appliances", "subcategory": "Cooling", "source": "seed", "product_url": "https://example.com/samsung-refrigerator", "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80", "description": "Spacious and modern refrigerator with good cooling consistency and convenience features.", "features": "Cooling;Capacity;Features;Durability;Price", "price": "₹66,999"},
    {"name": "Whirlpool Refrigerator", "brand": "Whirlpool", "category": "Home Appliances", "subcategory": "Cooling", "source": "seed", "product_url": "https://example.com/whirlpool-refrigerator", "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80", "description": "Dependable and practical cooling with a comfortable user experience and consistent performance.", "features": "Cooling;Capacity;Price;Durability;Features", "price": "₹54,999"},
    {"name": "Philips Air Fryer", "brand": "Philips", "category": "Home Appliances", "subcategory": "Cooking", "source": "seed", "product_url": "https://example.com/philips-air-fryer", "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80", "description": "Healthy cooking appliance with quick heating and easy cleanup advantages.", "features": "Features;Performance;Ease of Use;Price;Durability", "price": "₹8,499"},
    {"name": "Prestige Air Fryer", "brand": "Prestige", "category": "Home Appliances", "subcategory": "Cooking", "source": "seed", "product_url": "https://example.com/prestige-air-fryer", "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80", "description": "Compact air fryer that makes quick, convenient cooking a practical use case.", "features": "Price;Features;Performance;Ease of Use;Durability", "price": "₹6,999"},
    {"name": "Philips Mixer", "brand": "Philips", "category": "Home Appliances", "subcategory": "Kitchen Appliances", "source": "seed", "product_url": "https://example.com/philips-mixer", "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80", "description": "Efficient kitchen mixer for daily prep and reliable blending performance.", "features": "Performance;Price;Durability;Features;Ease of Use", "price": "₹4,499"},
    {"name": "Bajaj Mixer", "brand": "Bajaj", "category": "Home Appliances", "subcategory": "Kitchen Appliances", "source": "seed", "product_url": "https://example.com/bajaj-mixer", "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80", "description": "Affordable blender and mixer with dependable performance for home kitchens.", "features": "Price;Performance;Features;Durability;Ease of Use", "price": "₹3,499"},

    # Beauty
    {"name": "Dyson Airwrap", "brand": "Dyson", "category": "Beauty", "subcategory": "Hair Styling", "source": "seed", "product_url": "https://example.com/dyson-airwrap", "image_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80", "description": "High-end hair styling tool with premium design and easy styling performance.", "features": "Features;Build Quality;Performance;Price;Design", "price": "₹49,999"},
    {"name": "Philips Trimmer", "brand": "Philips", "category": "Beauty", "subcategory": "Grooming", "source": "seed", "product_url": "https://example.com/philips-trimmer", "image_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80", "description": "Easy-to-use grooming tool with good precision and long-lasting battery performance.", "features": "Performance;Battery;Price;Comfort;Features", "price": "₹1,999"},
    {"name": "Philips Hair Dryer", "brand": "Philips", "category": "Beauty", "subcategory": "Hair Styling", "source": "seed", "product_url": "https://example.com/philips-hair-dryer", "image_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80", "description": "Powerful hair dryer with a comfortable handle and useful styling options.", "features": "Performance;Features;Price;Comfort;Durability", "price": "₹3,299"},
    {"name": "Braun Trimmer", "brand": "Braun", "category": "Beauty", "subcategory": "Grooming", "source": "seed", "product_url": "https://example.com/braun-trimmer", "image_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80", "description": "Premium grooming tool with smooth trimming performance and durable build.", "features": "Performance;Build Quality;Comfort;Battery;Price", "price": "₹3,999"},
    {"name": "Mamaearth products", "brand": "Mamaearth", "category": "Beauty", "subcategory": "Skincare", "source": "seed", "product_url": "https://example.com/mamaearth-products", "image_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80", "description": "Natural skincare range with a value-conscious positioning and gentleness appeal.", "features": "Price;Features;Comfort;Skin Feel;Customer Service", "price": "₹699"},
    {"name": "Minimalist products", "brand": "Minimalist", "category": "Beauty", "subcategory": "Skincare", "source": "seed", "product_url": "https://example.com/minimalist-products", "image_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80", "description": "Ingredient-led skincare solutions with a minimal, user-friendly positioning.", "features": "Features;Skin Feel;Price;Customer Service;Results", "price": "₹799"},
    {"name": "Cetaphil products", "brand": "Cetaphil", "category": "Beauty", "subcategory": "Skincare", "source": "seed", "product_url": "https://example.com/cetaphil-products", "image_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80", "description": "Gentle skincare staples trusted for sensitive skin and daily comfort.", "features": "Skin Feel;Comfort;Results;Price;Customer Service", "price": "₹899"},
    {"name": "CeraVe products", "brand": "CeraVe", "category": "Beauty", "subcategory": "Skincare", "source": "seed", "product_url": "https://example.com/cerave-products", "image_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80", "description": "Dermatologist-friendly skincare with strong barrier support and easy routines.", "features": "Skin Feel;Results;Comfort;Price;Customer Service", "price": "₹949"},

    # Fitness
    {"name": "Yoga Mat", "brand": "Generic", "category": "Fitness", "subcategory": "Exercise", "source": "seed", "product_url": "https://example.com/yoga-mat", "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80", "description": "Comfortable and durable mat for home workouts and mobility sessions.", "features": "Comfort;Durability;Price;Performance;Grip", "price": "₹1,499"},
    {"name": "Dumbbells", "brand": "Generic", "category": "Fitness", "subcategory": "Weights", "source": "seed", "product_url": "https://example.com/dumbbells", "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80", "description": "Standard weights for strength training and progressive home workouts.", "features": "Durability;Performance;Price;Comfort;Features", "price": "₹2,499"},
    {"name": "Treadmill", "brand": "Generic", "category": "Fitness", "subcategory": "Cardio", "source": "seed", "product_url": "https://example.com/treadmill", "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80", "description": "Exercise machine built for consistent cardio and home fitness routines.", "features": "Performance;Durability;Features;Price;Comfort", "price": "₹29,999"},
    {"name": "Resistance Bands", "brand": "Generic", "category": "Fitness", "subcategory": "Exercise", "source": "seed", "product_url": "https://example.com/resistance-bands", "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80", "description": "Portable strength accessory that supports mobility and resistance training.", "features": "Price;Durability;Comfort;Performance;Features", "price": "₹799"},
    {"name": "Smart Fitness Bands", "brand": "Generic", "category": "Fitness", "subcategory": "Wearables", "source": "seed", "product_url": "https://example.com/smart-fitness-bands", "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80", "description": "Wearables that help track activity, heart rate, and daily movement.", "features": "Features;Battery;Comfort;Price;Performance", "price": "₹2,299"},
    {"name": "Protein Shaker", "brand": "Generic", "category": "Fitness", "subcategory": "Supplements", "source": "seed", "product_url": "https://example.com/protein-shaker", "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80", "description": "Useful gym accessory with durable build and easy everyday portability.", "features": "Price;Durability;Features;Ease of Use;Comfort", "price": "₹399"},

    # Fashion
    {"name": "Nike shoes", "brand": "Nike", "category": "Fashion", "subcategory": "Footwear", "source": "seed", "product_url": "https://example.com/nike-shoes", "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80", "description": "Performance-focused footwear with a strong reputation for comfort and style.", "features": "Comfort;Performance;Design;Durability;Price", "price": "₹4,999"},
    {"name": "Adidas shoes", "brand": "Adidas", "category": "Fashion", "subcategory": "Footwear", "source": "seed", "product_url": "https://example.com/adidas-shoes", "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80", "description": "Versatile sneakers known for comfort, reliability, and everyday wearability.", "features": "Comfort;Design;Price;Performance;Durability", "price": "₹4,499"},
    {"name": "Puma shoes", "brand": "Puma", "category": "Fashion", "subcategory": "Footwear", "source": "seed", "product_url": "https://example.com/puma-shoes", "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80", "description": "Sporty footwear delivering everyday versatility with a fashionable silhouette.", "features": "Style;Comfort;Price;Performance;Durability", "price": "₹3,699"},
    {"name": "Levi's jeans", "brand": "Levi's", "category": "Fashion", "subcategory": "Apparel", "source": "seed", "product_url": "https://example.com/levis-jeans", "image_url": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=900&q=80", "description": "Classic denim staple with reliable fit and brand recognition in everyday wear.", "features": "Comfort;Durability;Style;Fit;Price", "price": "₹2,499"},
    {"name": "Allen Solly shirts", "brand": "Allen Solly", "category": "Fashion", "subcategory": "Apparel", "source": "seed", "product_url": "https://example.com/allen-solly-shirts", "image_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80", "description": "Smart casual shirts known for comfort, fit, and polished office-friendly styling.", "features": "Comfort;Fit;Style;Price;Fabric", "price": "₹1,899"},
    {"name": "Peter England shirts", "brand": "Peter England", "category": "Fashion", "subcategory": "Apparel", "source": "seed", "product_url": "https://example.com/peter-england-shirts", "image_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80", "description": "Classic businesswear shirts that offer a practical and comfortable style choice.", "features": "Comfort;Fit;Style;Price;Fabric", "price": "₹1,699"},
    {"name": "Wildcraft bags", "brand": "Wildcraft", "category": "Fashion", "subcategory": "Accessories", "source": "seed", "product_url": "https://example.com/wildcraft-bags", "image_url": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=900&q=80", "description": "Travel-friendly bags valued for utility, storage space, and sturdiness.", "features": "Durability;Storage;Price;Design;Comfort", "price": "₹1,999"},
    {"name": "American Tourister bags", "brand": "American Tourister", "category": "Fashion", "subcategory": "Accessories", "source": "seed", "product_url": "https://example.com/american-tourister-bags", "image_url": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=900&q=80", "description": "Popular luggage and bags focused on travel convenience and ruggedness.", "features": "Durability;Design;Storage;Price;Features", "price": "₹3,299"},

    # Books
    {"name": "Popular programming books", "brand": "Various", "category": "Books", "subcategory": "Programming", "source": "seed", "product_url": "https://example.com/popular-programming-books", "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=80", "description": "Top-rated programming titles that help learners improve technical understanding.", "features": "Learning;Depth;Clarity;Price;Value", "price": "₹799"},
    {"name": "Self-development books", "brand": "Various", "category": "Books", "subcategory": "Personal Growth", "source": "seed", "product_url": "https://example.com/self-development-books", "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=80", "description": "Books designed to support productivity, habit-building, and personal improvement.", "features": "Learning;Value;Clarity;Price;Practicality", "price": "₹699"},
    {"name": "Engineering books", "brand": "Various", "category": "Books", "subcategory": "Academic", "source": "seed", "product_url": "https://example.com/engineering-books", "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=80", "description": "Technical books built to reinforce engineering fundamentals and applied knowledge.", "features": "Depth;Clarity;Value;Learning;Price", "price": "₹899"},
    {"name": "Fiction books", "brand": "Various", "category": "Books", "subcategory": "Literature", "source": "seed", "product_url": "https://example.com/fiction-books", "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=80", "description": "Stories that offer immersive worlds, memorable characters, and engaging reading experiences.", "features": "Storytelling;Value;Learning;Price;Enjoyment", "price": "₹599"},

    # Gaming
    {"name": "PlayStation 5", "brand": "Sony", "category": "Gaming", "subcategory": "Consoles", "source": "seed", "product_url": "https://example.com/playstation-5", "image_url": "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?auto=format&fit=crop&w=900&q=80", "description": "Console performance and premium graphics paired with a broad game library.", "features": "Performance;Features;Display;Price;Build Quality", "price": "₹49,990"},
    {"name": "Xbox Series X", "brand": "Microsoft", "category": "Gaming", "subcategory": "Consoles", "source": "seed", "product_url": "https://example.com/xbox-series-x", "image_url": "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?auto=format&fit=crop&w=900&q=80", "description": "High-performance console with strong graphics, media features, and online capabilities.", "features": "Performance;Features;Price;Display;Build Quality", "price": "₹49,990"},
    {"name": "Nintendo Switch", "brand": "Nintendo", "category": "Gaming", "subcategory": "Portable Consoles", "source": "seed", "product_url": "https://example.com/nintendo-switch", "image_url": "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?auto=format&fit=crop&w=900&q=80", "description": "Versatile hybrid console for both home and portable gaming sessions.", "features": "Features;Portability;Performance;Price;Comfort", "price": "₹29,990"},
    {"name": "Gaming keyboards", "brand": "Various", "category": "Gaming", "subcategory": "Peripherals", "source": "seed", "product_url": "https://example.com/gaming-keyboards", "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=900&q=80", "description": "Mechanical keyboards built for responsiveness, comfort, and immersive gameplay.", "features": "Performance;Comfort;Build Quality;Features;Price", "price": "₹4,999"},
    {"name": "Gaming mice", "brand": "Various", "category": "Gaming", "subcategory": "Peripherals", "source": "seed", "product_url": "https://example.com/gaming-mice", "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=900&q=80", "description": "Ergonomic pointing devices tuned for speed, precision, and comfortable handling.", "features": "Performance;Comfort;Features;Price;Durability", "price": "₹2,999"},
    {"name": "Gaming headphones", "brand": "Various", "category": "Gaming", "subcategory": "Audio", "source": "seed", "product_url": "https://example.com/gaming-headphones", "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=900&q=80", "description": "Audio gear prioritized for clarity, immersion, and comfort during long sessions.", "features": "Sound;Comfort;Features;Battery;Price", "price": "₹5,999"},
    {"name": "Gaming monitors", "brand": "Various", "category": "Gaming", "subcategory": "Displays", "source": "seed", "product_url": "https://example.com/gaming-monitors", "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=900&q=80", "description": "Displays tuned for refresh rate, clarity, and smoother competitive gaming experiences.", "features": "Display;Performance;Features;Price;Build Quality", "price": "₹18,999"},
]

SOURCE_DEMO_PRODUCTS = [
    {
        "name": "Nike Air Max",
        "brand": "Nike",
        "category": "Fashion",
        "subcategory": "Athletic Footwear",
        "source": "seeded_demo",
        "product_url": None,
        "image_url": None,
        "description": "Synthetic demo catalog identity for source-specific analysis; no live listing is asserted.",
        "features": "Comfort;Performance;Fit;Durability;Design",
        "price": None,
    },
]

SEED_CATALOG = PRODUCT_CATALOG + build_additional_products() + SOURCE_DEMO_PRODUCTS

SOURCE_DEMO_LISTINGS = {
    "amazon": ("iPhone 15",),
    "flipkart": ("iPhone 15",),
    "myntra": ("Nike Air Max", "Nike shoes"),
    "ajio": ("Nike Air Max", "Adidas shoes"),
    "meesho": ("Adidas shoes", "Levi's jeans"),
    "snapdeal": ("boAt Airdopes",),
    "tatacliq": ("iPhone 15", "Samsung Galaxy S24"),
    "nykaa": ("CeraVe products", "Minimalist products"),
    "croma": ("iPhone 15", "MacBook Air M2"),
    "reliance_digital": ("iPhone 15", "Samsung Smart TV"),
    "bigbasket": ("Tata Sampann Toor Dal 1kg",),
    "blinkit": ("Amul Taaza Toned Milk 1L",),
    "zepto": ("Haldiram's Aloo Bhujia Snack",),
    "swiggy_instamart": ("Aashirvaad Whole Wheat Atta 5kg",),
    "jiomart": ("Fortune Sunflower Oil 1L",),
    "firstcry": ("FirstCry Babyhug Car Seat",),
    "pepperfry": ("Pepperfry Oslo 3-Seater Sofa",),
    "lenskart": ("Lenskart Air Flex Rectangle Frames",),
    "decathlon": ("Decathlon Domyos 500 Yoga Mat",),
    "ikea": ("IKEA MALM Bed Frame",),
}

ASPECT_REVIEWS = [
    # Positive reviews with aspects
    ("The camera is exceptional with crisp low-light photos, and the battery life lasts easily through a full heavy workday.", 5, "positive"),
    ("Impressive build quality and stunning display colors. The performance is smooth and responsive throughout.", 5, "positive"),
    ("Sound clarity is fantastic with deep bass. The comfort during long hours is unmatched and worth the price.", 5, "positive"),
    ("Fast charging is super convenient and the software UI is clean without any annoying bloatware.", 4, "positive"),
    ("Solid durability and great ergonomics. Has survived everyday drops easily and looks very sleek in design.", 5, "positive"),
    ("Excellent value for price with reliable performance and snappy response across all daily applications.", 4, "positive"),
    ("The display refresh rate is ultra-smooth and the battery backup is very dependable for travelers.", 5, "positive"),

    # Neutral reviews with mixed aspects
    ("The camera is decent in daytime but battery life is just average. Good enough for casual use.", 3, "neutral"),
    ("Display quality is bright and clear, but the software has minor glitches and charging is slightly slow.", 3, "neutral"),
    ("Comfortable fit and reasonable sound, but build quality feels somewhat plastic for the price point.", 3, "neutral"),
    ("Performance handles regular tasks fine, though it warms up during extended gaming sessions.", 3, "neutral"),
    ("Acceptable durability and clean design, though customer support could be more responsive.", 3, "neutral"),

    # Negative reviews with aspects
    ("Battery life is poor and drains fast, while the performance lags frequently under normal multi-tasking.", 1, "negative"),
    ("Disappointing build quality and the software is filled with bugs and stutters. Definitely overpriced.", 2, "negative"),
    ("Camera quality is grainy in indoor lighting and charging speed is painfully slow.", 2, "negative"),
    ("Uncomfortable to wear for more than 30 minutes, and the sound has noticeable background distortion.", 1, "negative"),
    ("Poor durability as the material started creaking within two weeks. Frustrating experience for the price.", 2, "negative"),
]


def build_reviews(product_name: str, product_index: int):
    import random
    from datetime import datetime, timedelta

    # Deterministic seed based on product_index
    rnd = random.Random(product_index * 42 + 7)
    reviews_count = rnd.randint(6, 12)
    selected_reviews = []

    now = datetime.utcnow()
    for i in range(reviews_count):
        # 60% positive, 25% neutral, 15% negative distribution for realistic high-rated tech products
        rand_val = rnd.random()
        if rand_val < 0.60:
            candidates = [r for r in ASPECT_REVIEWS if r[2] == "positive"]
        elif rand_val < 0.85:
            candidates = [r for r in ASPECT_REVIEWS if r[2] == "neutral"]
        else:
            candidates = [r for r in ASPECT_REVIEWS if r[2] == "negative"]

        template = rnd.choice(candidates)
        days_ago = rnd.randint(1, 180)
        review_date = now - timedelta(days=days_ago)

        reviewer_first_names = ["Aarav", "Priya", "Rahul", "Ananya", "Vikram", "Sneha", "Karthik", "Pooja", "Arjun", "Divya", "Rohan", "Meera", "Kabir", "Neha", "Aditya"]
        reviewer_name = f"{rnd.choice(reviewer_first_names)} {chr(65 + (product_index + i) % 26)}."

        selected_reviews.append({
            "reviewer_name": reviewer_name,
            "review_text": template[0],
            "rating": template[1],
            "review_date": review_date,
            "source": "seed",
            "is_demo": True,
            "verified_purchase": rnd.random() > 0.15,
        })
    return selected_reviews


def seed_source_demo_evidence(session: Session, analyzer: SentimentAnalyzerService | None = None) -> int:
    import json
    import re
    from datetime import datetime, timedelta

    analyzer = analyzer or SentimentAnalyzerService()
    for product_payload in SOURCE_DEMO_PRODUCTS:
        product = session.query(Product).filter(Product.name == product_payload["name"]).first()
        if product is None:
            product = Product(
                **product_payload,
                platform="amazon",
                average_rating=0.0,
                total_reviews=0,
                is_demo=True,
            )
            session.add(product)
    session.flush()

    source_order = {source.code: index for index, source in enumerate(SUPPORTED_SOURCES)}
    source_labels = {source.code: source.name for source in SUPPORTED_SOURCES}
    inserted_reviews = 0

    for source_code, product_names in SOURCE_DEMO_LISTINGS.items():
        if source_code not in source_labels:
            continue
        for listing_index, product_name in enumerate(product_names):
            product = session.query(Product).filter(Product.name == product_name).first()
            if product is None or not product.is_demo:
                continue

            source_listing = session.query(ProductSource).filter_by(
                product_id=product.id,
                source_name=source_code,
            ).first()
            if source_listing is None:
                source_listing = ProductSource(
                    product_id=product.id,
                    source_name=source_code,
                    product_url=None,
                    source_product_id=None,
                    data_type="seeded_demo",
                )
                session.add(source_listing)
                session.flush()
            elif source_listing.data_type != "seeded_demo":
                continue

            existing_verified_observation = session.query(SourceObservation).filter(
                SourceObservation.product_source_id == source_listing.id,
                SourceObservation.data_type.in_(("stored", "live_scraped")),
            ).first()
            if existing_verified_observation is not None:
                continue

            review_samples = [
                ("The display is clear and the performance feels smooth in everyday use.", 5),
                ("Setup was straightforward and the product feels comfortable for regular use.", 4),
                ("It works as expected, although the fit and build quality feel average.", 3),
                ("The experience was disappointing, with frustrating performance and durability.", 2),
            ]
            source_reviews = []
            for review_index, (review_text, rating) in enumerate(review_samples):
                reviewer_name = f"ReviewLens demo {source_code} {review_index + 1}"
                review = session.query(Review).filter(
                    Review.product_id == product.id,
                    Review.source_id == source_listing.id,
                    Review.reviewer_name == reviewer_name,
                    Review.review_text == review_text,
                ).first()
                if review is None:
                    review = Review(
                        product_id=product.id,
                        source_id=source_listing.id,
                        reviewer_name=reviewer_name,
                        review_text=review_text,
                        rating=rating,
                        review_date=datetime.utcnow() - timedelta(days=review_index * 34 + source_order[source_code]),
                        source=source_code,
                        is_demo=True,
                        data_type="seeded_demo",
                        verified_purchase=False,
                    )
                    session.add(review)
                    session.flush()

                    sentiment = analyzer.analyze(review.review_text, rating=rating, verified_purchase=False)
                    sentiment_result = SentimentResult(
                        review_id=review.id,
                        sentiment_label=sentiment["sentiment_label"],
                        sentiment_score=sentiment["confidence_score"],
                        compound_score=sentiment["compound_score"],
                        positive_score=sentiment["positive_score"],
                        neutral_score=sentiment["neutral_score"],
                        negative_score=sentiment["negative_score"],
                        polarity_score=sentiment["polarity_score"],
                        subjectivity_score=sentiment["subjectivity_score"],
                        confidence_score=sentiment["confidence_score"],
                        aspects_json=json.dumps(sentiment["aspects"]),
                        quality_score=sentiment["quality_score"],
                    )
                    session.add(sentiment_result)
                    session.flush()
                    inserted_reviews += 1
                    review = session.query(Review).filter(Review.id == review.id).first()

                source_reviews.append(review)
                if review.sentiment and review.sentiment.aspects_json:
                    aspects = json.loads(review.sentiment.aspects_json or "{}")
                    for aspect_name, details in aspects.items():
                        existing_aspect = session.query(ReviewAspect).filter_by(
                            review_id=review.id,
                            aspect=aspect_name,
                        ).first()
                        if existing_aspect is None:
                            session.add(ReviewAspect(
                                review_id=review.id,
                                aspect=aspect_name,
                                sentiment=details.get("sentiment", "neutral"),
                                score=details.get("compound", 0.0),
                            ))

            existing_observation = session.query(SourceObservation).filter(
                SourceObservation.product_source_id == source_listing.id,
            ).first()
            if existing_observation is None:
                price_digits = re.sub(r"[^0-9.]", "", product.price or "")
                base_price = float(price_digits) if price_digits else None
                adjustment = ((source_order[source_code] + listing_index) % 5 - 2) * 0.01
                demo_price = round(base_price * (1 + adjustment), 2) if base_price is not None else None
                average_rating = round(sum(review.rating for review in source_reviews) / len(source_reviews), 2) if source_reviews else None
                session.add(SourceObservation(
                    product_source_id=source_listing.id,
                    price=demo_price,
                    currency="INR" if demo_price is not None else None,
                    rating=average_rating,
                    review_count=len(source_reviews) if source_reviews else None,
                    availability=None,
                    data_type="seeded_demo",
                ))

            all_reviews = session.query(Review).filter(Review.product_id == product.id).all()
            if all_reviews:
                product.average_rating = round(sum(review.rating for review in all_reviews) / len(all_reviews), 2)
                product.total_reviews = len(all_reviews)

    session.flush()
    return inserted_reviews


def seed_database() -> int:
    import json
    from app.database.database import _safe_migrate_columns
    Base.metadata.create_all(bind=engine)
    _safe_migrate_columns()

    analyzer = SentimentAnalyzerService()
    with Session(bind=engine) as session:
        count = 0
        for idx, product_payload in enumerate(SEED_CATALOG):
            product = session.query(Product).filter(Product.name == product_payload["name"]).first()
            if product is not None and not product.is_demo:
                continue
            if product is None:
                product = Product(
                    name=product_payload["name"],
                    brand=product_payload["brand"],
                    category=product_payload["category"],
                    subcategory=product_payload["subcategory"],
                    source=product_payload["source"],
                    product_url=product_payload["product_url"],
                    image_url=product_payload["image_url"],
                    description=product_payload["description"],
                    features=product_payload["features"],
                    price=product_payload["price"],
                    platform="amazon",
                    average_rating=4.0,
                    total_reviews=0,
                    is_demo=True,
                )
                session.add(product)
                session.flush()
            else:
                # Update category in case it was updated (e.g. Tablets, Headphones, Earbuds)
                product.category = product_payload["category"]
                product.subcategory = product_payload["subcategory"]
                product.features = product_payload["features"]
                product.price = product_payload["price"]

            if idx >= len(PRODUCT_CATALOG):
                session.commit()
                continue

            for review_data in build_reviews(product_payload["name"], idx):
                review = session.query(Review).filter(
                    Review.product_id == product.id,
                    Review.reviewer_name == review_data["reviewer_name"],
                    Review.review_text == review_data["review_text"],
                ).first()
                if review is None:
                    review = Review(
                        product_id=product.id,
                        reviewer_name=review_data["reviewer_name"],
                        review_text=review_data["review_text"],
                        rating=review_data["rating"],
                        review_date=review_data["review_date"],
                        source=review_data["source"],
                        is_demo=review_data["is_demo"],
                        data_type="seeded_demo",
                        verified_purchase=review_data["verified_purchase"],
                    )
                    session.add(review)
                    session.flush()

                    sentiment = analyzer.analyze(review.review_text, rating=review.rating, verified_purchase=review.verified_purchase)
                    sentiment_result = SentimentResult(
                            review_id=review.id,
                            sentiment_label=sentiment["sentiment_label"],
                            sentiment_score=sentiment["confidence_score"],
                            compound_score=sentiment["compound_score"],
                            positive_score=sentiment["positive_score"],
                            neutral_score=sentiment["neutral_score"],
                            negative_score=sentiment["negative_score"],
                            polarity_score=sentiment.get("polarity_score", 0.0),
                            subjectivity_score=sentiment.get("subjectivity_score", 0.0),
                            confidence_score=sentiment.get("confidence_score", 0.0),
                            aspects_json=json.dumps(sentiment.get("aspects", {})),
                            quality_score=sentiment.get("quality_score", 1.0),
                        )
                    session.add(sentiment_result)
                    session.flush()
                    count += 1

                if review.sentiment and review.sentiment.aspects_json:
                    aspects = json.loads(review.sentiment.aspects_json)
                    for aspect_name, details in aspects.items():
                        aspect_row = session.query(ReviewAspect).filter_by(
                            review_id=review.id,
                            aspect=aspect_name,
                        ).first()
                        if aspect_row is None:
                            session.add(
                                ReviewAspect(
                                    review_id=review.id,
                                    aspect=aspect_name,
                                    sentiment=details.get("sentiment", "neutral"),
                                    score=details.get("compound", 0.0),
                                )
                            )

            if product.reviews:
                product.average_rating = round(sum(review.rating for review in product.reviews) / len(product.reviews), 2)
                product.total_reviews = len(product.reviews)
            session.commit()

        count += seed_source_demo_evidence(session, analyzer)
        session.commit()

    return count


if __name__ == "__main__":
    inserted = seed_database()
    print(f"Seeded {inserted} demo reviews across {len(SEED_CATALOG)} products.")
