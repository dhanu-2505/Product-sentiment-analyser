from app.sources.base_source import SourceDefinition

SUPPORTED_SOURCES = (
    SourceDefinition("amazon", "Amazon", "https://www.amazon.in", live_connector_configured=True),
    SourceDefinition("flipkart", "Flipkart", "https://www.flipkart.com", live_connector_configured=True),
    SourceDefinition("myntra", "Myntra", "https://www.myntra.com"),
    SourceDefinition("ajio", "AJIO", "https://www.ajio.com"),
    SourceDefinition("meesho", "Meesho", "https://www.meesho.com"),
    SourceDefinition("snapdeal", "Snapdeal", "https://www.snapdeal.com"),
    SourceDefinition("tatacliq", "Tata CLiQ", "https://www.tatacliq.com"),
    SourceDefinition("nykaa", "Nykaa", "https://www.nykaa.com"),
    SourceDefinition("croma", "Croma", "https://www.croma.com"),
    SourceDefinition("reliance_digital", "Reliance Digital", "https://www.reliancedigital.in"),
    SourceDefinition("bigbasket", "BigBasket", "https://www.bigbasket.com"),
    SourceDefinition("blinkit", "Blinkit", "https://blinkit.com"),
    SourceDefinition("zepto", "Zepto", "https://www.zepto.com"),
    SourceDefinition("swiggy_instamart", "Swiggy Instamart", "https://www.swiggy.com/instamart"),
    SourceDefinition("jiomart", "JioMart", "https://www.jiomart.com"),
    SourceDefinition("firstcry", "FirstCry", "https://www.firstcry.com"),
    SourceDefinition("pepperfry", "Pepperfry", "https://www.pepperfry.com"),
    SourceDefinition("lenskart", "Lenskart", "https://www.lenskart.com"),
    SourceDefinition("decathlon", "Decathlon", "https://www.decathlon.in"),
    SourceDefinition("ikea", "IKEA", "https://www.ikea.com/in/en"),
)
