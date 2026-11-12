from __future__ import annotations


ADDITIONAL_PRODUCT_GROUPS = {
    "Smartphones": [
        ("Samsung", "Galaxy A55"), ("Samsung", "Galaxy Z Fold5"), ("Samsung", "Galaxy Z Flip5"),
        ("Google", "Pixel 7a"), ("Google", "Pixel 8a"), ("Google", "Pixel 9 Pro"),
        ("Xiaomi", "Redmi Note 12 Pro"), ("Xiaomi", "Redmi Note 13 Pro+"), ("Xiaomi", "Xiaomi 14"),
        ("Xiaomi", "Xiaomi 14 Ultra"), ("OnePlus", "Nord CE4"), ("OnePlus", "Nord 4"),
        ("Realme", "12 Pro+"), ("Oppo", "Find X7"), ("Vivo", "X100"), ("Motorola", "Razr 50"),
    ],
    "Laptops": [
        ("Apple", "MacBook Air M1"), ("Apple", "MacBook Pro M3"), ("Dell", "Latitude 5450"),
        ("Dell", "G15"), ("HP", "ProBook 440"), ("Lenovo", "Yoga Slim 7"),
        ("Lenovo", "ThinkPad E14"), ("ASUS", "Zenbook 14"), ("ASUS", "ROG Zephyrus G14"),
        ("Acer", "Swift Go 14"), ("MSI", "Katana 15"), ("Microsoft", "Surface Laptop 6"),
    ],
    "Tablets": [
        ("Apple", "iPad 10th Generation"), ("Samsung", "Galaxy Tab A9"), ("Xiaomi", "Pad 6"),
        ("Lenovo", "Tab M10"), ("Honor", "Pad 9"), ("OnePlus", "Pad Go"),
    ],
    "Headphones": [
        ("Sony", "WH-CH720N"), ("Sony", "WH-XB910N"), ("Bose", "QuietComfort Ultra"),
        ("JBL", "Live 770NC"), ("Sennheiser", "Accentum Plus"), ("Audio-Technica", "ATH-M50xBT2"),
    ],
    "Earbuds": [
        ("Sony", "WF-1000XM5"), ("Samsung", "Galaxy Buds FE"), ("Google", "Pixel Buds Pro"),
        ("Jabra", "Elite 8 Active"), ("boAt", "Nirvana Ion"), ("Nothing", "Ear (a)"),
    ],
    "Smartwatches": [
        ("Apple", "Watch Series 9"), ("Samsung", "Galaxy Watch6 Classic"), ("Garmin", "Venu 3"),
        ("Amazfit", "Balance"), ("Noise", "ColorFit Pro 5"), ("Fitbit", "Charge 6"),
    ],
    "TVs": [
        ("Samsung", "The Frame TV"), ("LG", "C3 OLED TV"), ("Sony", "Bravia X90L"),
        ("TCL", "C755 QD-Mini LED TV"), ("Xiaomi", "X Pro QLED TV"),
    ],
    "Cameras": [
        ("Canon", "EOS R50"), ("Nikon", "Z50 II"), ("Sony", "Alpha A6700"),
        ("Fujifilm", "X-S20"), ("GoPro", "Hero12 Black"),
    ],
    "Home Appliances": [
        ("LG", "Front Load Washer 9kg"), ("Samsung", "Bespoke Refrigerator"),
        ("Whirlpool", "6th Sense Refrigerator"), ("IFB", "Senator Washing Machine"),
        ("Philips", "Air Fryer 3000 Series"), ("Prestige", "Nutrifry Air Fryer"),
        ("Bajaj", "GX-1 Mixer Grinder"), ("Dyson", "V15 Detect Vacuum"),
        ("Eureka Forbes", "AquaSure Water Purifier"), ("Panasonic", "Inverter Microwave Oven"),
        ("Voltas", "Adjustable Inverter AC"), ("Havells", "Efficient Ceiling Fan"),
    ],
    "Beauty": [
        ("Dyson", "Supersonic Hair Dryer"), ("Philips", "Lumea IPL 9000"),
        ("Braun", "Silk-expert Pro 5"), ("Minimalist", "Salicylic Acid Cleanser"),
        ("Cetaphil", "Moisturizing Cream"),
    ],
    "Fashion": [
        ("Nike", "Pegasus 40 Running Shoes"), ("Adidas", "Ultraboost Light Shoes"),
        ("Puma", "Velocity Nitro 3 Shoes"), ("Levi's", "501 Original Jeans"),
        ("Allen Solly", "Regular Fit Oxford Shirt"), ("Peter England", "Slim Fit Formal Shirt"),
        ("Wildcraft", "Trailblazer 45 Backpack"), ("American Tourister", "Curio Spinner Luggage"),
    ],
    "Gaming": [
        ("Sony", "DualSense Edge Controller"), ("Microsoft", "Xbox Elite Wireless Controller"),
        ("Nintendo", "Switch OLED Model"), ("Logitech", "G Pro X TKL Keyboard"),
        ("Razer", "DeathAdder V3 Mouse"), ("LG", "UltraGear 27GP850 Monitor"),
        ("HyperX", "Cloud III Gaming Headset"), ("Corsair", "K70 RGB Pro Keyboard"),
    ],
    "Books": [
        ("Penguin Random House", "The Pragmatic Programmer"), ("O'Reilly", "Designing Data-Intensive Applications"),
        ("HarperCollins", "Atomic Habits"), ("Penguin Random House", "Project Hail Mary"),
        ("Pearson", "Introduction to Algorithms"),
    ],
    "Fitness": [
        ("Decathlon", "Domyos 500 Yoga Mat"), ("Decathlon", "Adjustable Dumbbell Set"),
        ("Cultsport", "Compact Home Treadmill"), ("Boldfit", "Resistance Band Set"),
        ("Fitbit", "Inspire 3 Tracker"), ("Nike", "Training Duffle Bag"),
    ],
    "Furniture": [
        ("IKEA", "MALM Bed Frame"), ("IKEA", "POANG Armchair"), ("IKEA", "LAGKAPTEN Desk"),
        ("Pepperfry", "Oslo 3-Seater Sofa"), ("Wakefit", "Ergo Study Chair"),
        ("Urban Ladder", "Mason Coffee Table"), ("Nilkamal", "Freedom Mini Cabinet"),
        ("Godrej Interio", "Motion Office Chair"),
    ],
    "Baby Products": [
        ("FirstCry", "Babyhug Car Seat"), ("Chicco", "KeyFit Infant Car Seat"),
        ("Philips Avent", "Natural Response Bottle Set"), ("Pampers", "Premium Care Diapers"),
        ("LuvLap", "Galaxy Stroller"), ("Fisher-Price", "Kick and Play Piano Gym"),
        ("Himalaya BabyCare", "Gentle Baby Lotion"), ("Mee Mee", "Electric Steam Sterilizer"),
    ],
    "Eyewear": [
        ("Lenskart", "Air Flex Rectangle Frames"), ("Ray-Ban", "Wayfarer Classic Sunglasses"),
        ("Oakley", "Holbrook Sunglasses"), ("Titan Eye+", "Blue Cut Computer Glasses"),
        ("Fastrack", "Urban Square Sunglasses"), ("John Jacobs", "Aviator Titanium Frames"),
    ],
    "Grocery": [
        ("Tata Sampann", "Toor Dal 1kg"), ("Aashirvaad", "Whole Wheat Atta 5kg"),
        ("Amul", "Taaza Toned Milk 1L"), ("Fortune", "Sunflower Oil 1L"),
        ("Organic India", "Tulsi Green Tea"), ("Haldiram's", "Aloo Bhujia Snack"),
        ("Dabur", "Honey 500g"), ("Tata Tea", "Gold Tea 1kg"),
    ],
}


def build_additional_products() -> list[dict[str, str | None]]:
    products = []
    for category, entries in ADDITIONAL_PRODUCT_GROUPS.items():
        for brand, model in entries:
            products.append({
                "name": f"{brand} {model}",
                "brand": brand,
                "category": category,
                "subcategory": category,
                "source": "seeded_demo",
                "product_url": None,
                "image_url": None,
                "description": "Synthetic demo catalog entry. No live source, price, or availability has been verified.",
                "features": None,
                "price": None,
            })
    return products
