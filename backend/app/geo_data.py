"""
geo_data.py: Comprehensive Global Geographic Hierarchy for Lead Intelligence Engine.

Provides hierarchical Country -> State/Province/Region -> Cities mapping
covering all major global commercial hubs, Gulf/MENA regions, North America,
Europe, Asia-Pacific, Latin America, and Africa.
"""

from typing import Any

# Hierarchy schema: { Country: { State/Province: [Cities...] } }
GEO_HIERARCHY: dict[str, dict[str, list[str]]] = {
    "United States": {
        "California": ["Los Angeles", "San Francisco", "San Diego", "San Jose", "Sacramento", "Oakland", "Fresno", "Irvine", "Long Beach", "Bakersfield", "Anaheim", "Santa Ana", "Riverside"],
        "New York": ["New York", "Buffalo", "Rochester", "Albany", "Syracuse", "Yonkers", "White Plains", "Ithaca"],
        "Texas": ["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth", "El Paso", "Arlington", "Plano", "Corpus Christi", "Lubbock", "Irving", "Frisco"],
        "Florida": ["Miami", "Orlando", "Tampa", "Jacksonville", "Fort Lauderdale", "St. Petersburg", "Tallahassee", "West Palm Beach", "Sarasota", "Cape Coral"],
        "Illinois": ["Chicago", "Aurora", "Naperville", "Rockford", "Springfield", "Peoria", "Elgin"],
        "Washington": ["Seattle", "Bellevue", "Spokane", "Tacoma", "Vancouver", "Everett", "Renton"],
        "Massachusetts": ["Boston", "Cambridge", "Worcester", "Springfield", "Lowell", "Quincy"],
        "Georgia": ["Atlanta", "Augusta", "Savannah", "Columbus", "Athens", "Macon"],
        "North Carolina": ["Charlotte", "Raleigh", "Greensboro", "Durham", "Winston-Salem", "Fayetteville", "Cary", "Wilmington"],
        "Pennsylvania": ["Philadelphia", "Pittsburgh", "Allentown", "Erie", "Reading", "Scranton"],
        "Ohio": ["Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron", "Dayton"],
        "Michigan": ["Detroit", "Grand Rapids", "Warren", "Sterling Heights", "Ann Arbor", "Lansing"],
        "Arizona": ["Phoenix", "Tucson", "Mesa", "Chandler", "Scottsdale", "Glendale", "Gilbert", "Tempe"],
        "Colorado": ["Denver", "Colorado Springs", "Aurora", "Fort Collins", "Lakewood", "Boulder"],
        "Virginia": ["Virginia Beach", "Norfolk", "Chesapeake", "Richmond", "Arlington", "Alexandria", "Tysons"],
        "New Jersey": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Trenton", "Princeton"],
        "Nevada": ["Las Vegas", "Henderson", "Reno", "North Las Vegas", "Sparks"],
        "Oregon": ["Portland", "Eugene", "Salem", "Gresham", "Hillsboro", "Beaverton"],
        "Tennessee": ["Nashville", "Memphis", "Knoxville", "Chattanooga", "Clarksville"],
        "Indiana": ["Indianapolis", "Fort Wayne", "Evansville", "South Bend", "Carmel"],
        "Missouri": ["Kansas City", "St. Louis", "Springfield", "Columbia", "Independence"],
        "Maryland": ["Baltimore", "Bethesda", "Silver Spring", "Frederick", "Rockville", "Gaithersburg"],
        "Wisconsin": ["Milwaukee", "Madison", "Green Bay", "Kenosha", "Racine"],
        "Minnesota": ["Minneapolis", "Saint Paul", "Rochester", "Bloomington", "Duluth"],
        "Utah": ["Salt Lake City", "West Valley City", "Provo", "West Jordan", "Orem", "Sandy"],
        "Alabama": ["Birmingham", "Huntsville", "Montgomery", "Mobile"],
        "Connecticut": ["Bridgeport", "New Haven", "Stamford", "Hartford", "Waterbury"],
        "South Carolina": ["Charleston", "Columbia", "Greenville", "Mount Pleasant"],
        "Kentucky": ["Louisville", "Lexington", "Bowling Green", "Owensboro"],
        "Louisiana": ["New Orleans", "Baton Rouge", "Shreveport", "Lafayette"],
        "Oklahoma": ["Oklahoma City", "Tulsa", "Norman", "Broken Arrow"],
        "Iowa": ["Des Moines", "Cedar Rapids", "Davenport", "Sioux City"],
        "Kansas": ["Wichita", "Overland Park", "Kansas City", "Olathe", "Topeka"],
        "Arkansas": ["Little Rock", "Fort Smith", "Fayetteville", "Springdale"],
        "Mississippi": ["Jackson", "Gulfport", "Southaven", "Biloxi"],
        "Nebraska": ["Omaha", "Lincoln", "Bellevue", "Grand Island"],
        "New Mexico": ["Albuquerque", "Las Cruces", "Rio Rancho", "Santa Fe"],
        "Idaho": ["Boise", "Meridian", "Nampa", "Idaho Falls"],
        "Hawaii": ["Honolulu", "Hilo", "Kailua", "Kapolei"],
        "New Hampshire": ["Manchester", "Nashua", "Concord"],
        "Maine": ["Portland", "Lewiston", "Bangor"],
        "Rhode Island": ["Providence", "Warwick", "Cranston"],
        "Montana": ["Billings", "Missoula", "Great Falls", "Bozeman"],
        "Delaware": ["Wilmington", "Dover", "Newark"],
        "South Dakota": ["Sioux Falls", "Rapid City", "Aberdeen"],
        "North Dakota": ["Fargo", "Bismarck", "Grand Forks"],
        "Alaska": ["Anchorage", "Fairbanks", "Juneau"],
        "Vermont": ["Burlington", "South Burlington", "Rutland"],
        "Wyoming": ["Cheyenne", "Casper", "Laramie"],
        "District of Columbia": ["Washington D.C."],
    },
    "Saudi Arabia": {
        "Riyadh Province": ["Riyadh", "Al-Kharj", "Ad-Diriyah", "Al-Majma'ah", "Dawadmi", "Wadi ad-Dawasir", "Al Zulfi"],
        "Makkah Province": ["Jeddah", "Makkah", "Taif", "Rabigh", "Al Qunfudhah", "Al Lith"],
        "Eastern Province": ["Dammam", "Al Khobar", "Dhahran", "Al Jubail", "Al Ahsa", "Qatif", "Hafar Al-Batin", "Ras Tanura", "Khafji"],
        "Madinah Province": ["Madinah", "Yanbu", "Al Ula", "Badr"],
        "Asir Province": ["Abha", "Khamis Mushait", "Bisha", "Muhayil"],
        "Tabuk Province": ["Tabuk", "NEOM", "Duba", "Al Wajh"],
        "Al-Qassim Province": ["Buraidah", "Unaizah", "Ar Rass", "Al Bukayriyah"],
        "Hail Province": ["Hail", "Baqaa"],
        "Jazan Province": ["Jazan", "Sabya", "Abu Arish", "Farasan"],
        "Najran Province": ["Najran", "Sharurah"],
        "Northern Borders": ["Arar", "Rafha", "Turaif"],
        "Al-Jawf Province": ["Sakaka", "Qurayyat", "Dumat al-Jandal"],
        "Al-Bahah Province": ["Al-Bahah", "Baljurashi", "Al Mandaq"],
    },
    "United Arab Emirates": {
        "Dubai": ["Dubai", "Jebel Ali", "Deira", "Bur Dubai", "Business Bay", "Dubai Silicon Oasis", "Dubai South", "Al Barsha"],
        "Abu Dhabi": ["Abu Dhabi", "Al Ain", "Al Dhafra", "Mussafah", "Khalifa City", "Yas Island"],
        "Sharjah": ["Sharjah", "Khor Fakkan", "Kalba", "Al Dhaid"],
        "Ajman": ["Ajman", "Masfout"],
        "Ras Al Khaimah": ["Ras Al Khaimah", "Al Jazirah Al Hamra"],
        "Fujairah": ["Fujairah", "Dibba Al-Fujairah"],
        "Umm Al Quwain": ["Umm Al Quwain"],
    },
    "United Kingdom": {
        "Greater London": ["London", "Westminster", "Camden", "Croydon", "Greenwich", "Kensington", "Stratford"],
        "North West": ["Manchester", "Liverpool", "Salford", "Preston", "Blackpool", "Bolton"],
        "West Midlands": ["Birmingham", "Coventry", "Wolverhampton", "Solihull", "Dudley"],
        "Yorkshire and the Humber": ["Leeds", "Sheffield", "Bradford", "York", "Hull", "Doncaster"],
        "South East": ["Brighton", "Southampton", "Portsmouth", "Oxford", "Reading", "Milton Keynes", "Slough"],
        "South West": ["Bristol", "Bath", "Plymouth", "Exeter", "Gloucester", "Cheltenham", "Bournemouth"],
        "East of England": ["Cambridge", "Norwich", "Luton", "Ipswich", "Peterborough", "Colchester"],
        "East Midlands": ["Nottingham", "Leicester", "Derby", "Northampton", "Lincoln"],
        "North East": ["Newcastle upon Tyne", "Sunderland", "Middlesbrough", "Durham"],
        "Scotland": ["Edinburgh", "Glasgow", "Aberdeen", "Dundee", "Inverness", "Stirling"],
        "Wales": ["Cardiff", "Swansea", "Newport", "Wrexham"],
        "Northern Ireland": ["Belfast", "Derry", "Lisburn", "Newry"],
    },
    "Canada": {
        "Ontario": ["Toronto", "Ottawa", "Mississauga", "Brampton", "Hamilton", "London", "Markham", "Vaughan", "Kitchener", "Waterloo", "Windsor"],
        "Quebec": ["Montreal", "Quebec City", "Laval", "Gatineau", "Longueuil", "Sherbrooke"],
        "British Columbia": ["Vancouver", "Victoria", "Surrey", "Burnaby", "Richmond", "Kelowna", "Abbotsford"],
        "Alberta": ["Calgary", "Edmonton", "Red Deer", "Lethbridge", "St. Albert"],
        "Manitoba": ["Winnipeg", "Brandon"],
        "Saskatchewan": ["Saskatoon", "Regina"],
        "Nova Scotia": ["Halifax", "Dartmouth", "Sydney"],
        "New Brunswick": ["Fredericton", "Moncton", "Saint John"],
        "Newfoundland and Labrador": ["St. John's"],
        "Prince Edward Island": ["Charlottetown"],
    },
    "Australia": {
        "New South Wales": ["Sydney", "Newcastle", "Wollongong", "Central Coast", "Parramatta"],
        "Victoria": ["Melbourne", "Geelong", "Ballarat", "Bendigo"],
        "Queensland": ["Brisbane", "Gold Coast", "Sunshine Coast", "Townsville", "Cairns"],
        "Western Australia": ["Perth", "Fremantle", "Mandurah", "Bunbury"],
        "South Australia": ["Adelaide", "Mount Gambier"],
        "Tasmania": ["Hobart", "Launceston"],
        "Australian Capital Territory": ["Canberra"],
        "Northern Territory": ["Darwin", "Alice Springs"],
    },
    "Germany": {
        "Berlin": ["Berlin"],
        "Bavaria": ["Munich", "Nuremberg", "Augsburg", "Regensburg", "Ingolstadt", "Würzburg"],
        "Hesse": ["Frankfurt", "Wiesbaden", "Kassel", "Darmstadt", "Offenbach"],
        "North Rhine-Westphalia": ["Cologne", "Düsseldorf", "Dortmund", "Essen", "Bonn", "Münster", "Aachen", "Duisburg"],
        "Baden-Württemberg": ["Stuttgart", "Karlsruhe", "Mannheim", "Freiburg", "Heidelberg", "Ulm"],
        "Hamburg": ["Hamburg"],
        "Lower Saxony": ["Hanover", "Braunschweig", "Osnabrück", "Oldenburg", "Göttingen"],
        "Saxony": ["Leipzig", "Dresden", "Chemnitz"],
        "Bremen": ["Bremen", "Bremerhaven"],
        "Rhineland-Palatinate": ["Mainz", "Ludwigshafen", "Koblenz", "Trier"],
        "Schleswig-Holstein": ["Kiel", "Lübeck"],
    },
    "France": {
        "Île-de-France": ["Paris", "Boulogne-Billancourt", "Saint-Denis", "Versailles", "Nanterre"],
        "Auvergne-Rhône-Alpes": ["Lyon", "Grenoble", "Saint-Étienne", "Clermont-Ferrand", "Annecy"],
        "Provence-Alpes-Côte d'Azur": ["Marseille", "Nice", "Toulon", "Aix-en-Provence", "Cannes", "Antibes"],
        "Occitanie": ["Toulouse", "Montpellier", "Nîmes", "Perpignan"],
        "Nouvelle-Aquitaine": ["Bordeaux", "Limoges", "Poitiers", "Pau", "La Rochelle"],
        "Grand Est": ["Strasbourg", "Reims", "Metz", "Nancy", "Mulhouse"],
        "Hauts-de-France": ["Lille", "Amiens", "Roubaix", "Tourcoing", "Calais"],
        "Pays de la Loire": ["Nantes", "Angers", "Le Mans"],
        "Brittany": ["Rennes", "Brest", "Quimper"],
        "Normandy": ["Rouen", "Le Havre", "Caen"],
    },
    "India": {
        "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik", "Navi Mumbai", "Aurangabad"],
        "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi", "Belagavi"],
        "Delhi NCR": ["New Delhi", "Gurugram", "Noida", "Faridabad", "Ghaziabad"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
        "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar"],
        "West Bengal": ["Kolkata", "Howrah", "Siliguri", "Durgapur"],
        "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi", "Prayagraj", "Meerut"],
        "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner"],
        "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode", "Thrissur"],
        "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Mohali"],
        "Madhya Pradesh": ["Indore", "Bhopal", "Jabalpur", "Gwalior"],
        "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Tirupati"],
    },
    "Singapore": {
        "Central Region": ["Singapore City", "Downtown Core", "Marina Bay", "Orchard", "Tanjong Pagar"],
        "East Region": ["Tampines", "Bedok", "Changi", "Pasir Ris"],
        "West Region": ["Jurong East", "Jurong West", "Clementi", "Tuas"],
        "North Region": ["Woodlands", "Yishun", "Sembawang"],
        "North-East Region": ["Sengkang", "Punggol", "Ang Mo Kio", "Hougang"],
    },
    "Qatar": {
        "Doha Municipality": ["Doha", "West Bay", "The Pearl", "Al Sadd"],
        "Al Rayyan": ["Al Rayyan", "Education City", "Abu Hamour"],
        "Al Daayen": ["Lusail"],
        "Al Wakrah": ["Al Wakrah", "Mesaieed"],
        "Al Khor": ["Al Khor", "Ras Laffan"],
        "Umm Salal": ["Umm Salal"],
    },
    "Kuwait": {
        "Al Asimah (Capital)": ["Kuwait City", "Sharq", "Mirqab", "Salhiya", "Dasman"],
        "Hawalli": ["Hawalli", "Salmiya", "Rumaithiya", "Jabriya"],
        "Farwaniya": ["Farwaniya", "Khaitan", "Jleeb Al-Shuyoukh", "Al Rai"],
        "Al Ahmadi": ["Ahmadi", "Fahaheel", "Mangaf", "Mahboula"],
        "Mubarak Al-Kabeer": ["Sabah Al-Salem", "Al-Qurain"],
        "Jahra": ["Al Jahra"],
    },
    "Bahrain": {
        "Capital Governorate": ["Manama", "Juffair", "Seef", "Diplomatic Area"],
        "Muharraq Governorate": ["Muharraq", "Busaiteen", "Amwaj Islands"],
        "Northern Governorate": ["Budaiya", "Saar", "Hamad Town"],
        "Southern Governorate": ["Riffa", "Isa Town", "Zallaq"],
    },
    "Oman": {
        "Muscat Governorate": ["Muscat", "Muttrah", "Bawshar", "Seeb", "Ruwi", "Al Khuwair"],
        "Dhofar Governorate": ["Salalah", "Taqah", "Mirbat"],
        "Al Batinah North": ["Sohar", "Shinas", "Liwa"],
        "Al Batinah South": ["Barka", "Rustaq"],
        "Al Dakhiliyah": ["Nizwa", "Bahla", "Samail"],
        "Al Sharqiyah": ["Sur", "Ibra"],
    },
    "Egypt": {
        "Cairo Governorate": ["Cairo", "New Cairo", "Nasr City", "Maadi", "Heliopolis", "Zamalek"],
        "Giza Governorate": ["Giza", "6th of October", "Sheikh Zayed City", "Dokki", "Mohandessin"],
        "Alexandria Governorate": ["Alexandria", "Borg El Arab", "Smouha", "Montaza"],
        "Sharqia Governorate": ["Zagazig", "10th of Ramadan"],
        "Dakahlia Governorate": ["Mansoura"],
        "Red Sea Governorate": ["Hurghada", "El Gouna"],
        "South Sinai": ["Sharm El Sheikh"],
    },
    "Japan": {
        "Tokyo": ["Tokyo", "Shinjuku", "Shibuya", "Chiyoda", "Minato", "Chuo", "Shinagawa"],
        "Osaka": ["Osaka", "Sakai", "Suita", "Higashiosaka"],
        "Kanagawa": ["Yokohama", "Kawasaki", "Sagamihara"],
        "Aichi": ["Nagoya", "Toyota", "Okazaki"],
        "Kyoto": ["Kyoto", "Uji"],
        "Fukuoka": ["Fukuoka", "Kitakyushu"],
        "Hokkaido": ["Sapporo", "Asahikawa", "Hakodate"],
        "Hyogo": ["Kobe", "Himeji", "Nishinomiya"],
        "Miyagi": ["Sendai"],
        "Hiroshima": ["Hiroshima", "Fukuyama"],
    },
    "China": {
        "Beijing Municipality": ["Beijing", "Chaoyang", "Haidian", "Dongcheng"],
        "Shanghai Municipality": ["Shanghai", "Pudong", "Huangpu", "Jing'an", "Xuhui"],
        "Guangdong": ["Guangzhou", "Shenzhen", "Dongguan", "Foshan", "Zhuhai", "Zhongshan"],
        "Zhejiang": ["Hangzhou", "Ningbo", "Wenzhou", "Yiwu", "Jiaxing"],
        "Jiangsu": ["Nanjing", "Suzhou", "Wuxi", "Changzhou"],
        "Sichuan": ["Chengdu", "Mianyang"],
        "Shandong": ["Qingdao", "Jinan", "Yantai"],
        "Hubei": ["Wuhan"],
        "Shaanxi": ["Xi'an"],
        "Chongqing Municipality": ["Chongqing"],
    },
    "Hong Kong": {
        "Hong Kong Island": ["Central", "Wan Chai", "Causeway Bay", "Admiralty"],
        "Kowloon": ["Tsim Sha Tsui", "Mong Kok", "Kwun Tong", "Kowloon Bay"],
        "New Territories": ["Sha Tin", "Tsuen Wan", "Tseung Kwan O", "Yuen Long"],
    },
    "South Korea": {
        "Seoul Capital Area": ["Seoul", "Gangnam", "Yeouido", "Jongno", "Mapo"],
        "Gyeonggi": ["Suwon", "Seongnam", "Pangyo", "Goyang", "Yongin", "Bucheon"],
        "Incheon": ["Incheon", "Songdo"],
        "Busan": ["Busan", "Haeundae"],
        "Daegu": ["Daegu"],
        "Daejeon": ["Daejeon"],
        "Gwangju": ["Gwangju"],
        "Ulsan": ["Ulsan"],
    },
    "Malaysia": {
        "Kuala Lumpur": ["Kuala Lumpur", "Bangsar", "Mont Kiara", "Bukit Bintang"],
        "Selangor": ["Petaling Jaya", "Shah Alam", "Subang Jaya", "Cyberjaya", "Klang"],
        "Penang": ["George Town", "Bayan Lepas", "Butterworth"],
        "Johor": ["Johor Bahru", "Iskandar Puteri"],
        "Sabah": ["Kota Kinabalu"],
        "Sarawak": ["Kuching", "Miri"],
    },
    "Indonesia": {
        "Jakarta Special Capital Region": ["Jakarta", "Central Jakarta", "South Jakarta", "West Jakarta"],
        "West Java": ["Bandung", "Bekasi", "Depok", "Bogor"],
        "East Java": ["Surabaya", "Malang", "Sidoarjo"],
        "Banten": ["Tangerang", "South Tangerang"],
        "Bali": ["Denpasar", "Badung", "Kuta", "Seminyak", "Ubud"],
        "North Sumatra": ["Medan"],
    },
    "Thailand": {
        "Bangkok Metropolitan": ["Bangkok", "Sathorn", "Sukhumvit", "Silom", "Chatuchak"],
        "Central": ["Nonthaburi", "Samut Prakan", "Pathum Thani"],
        "Eastern": ["Pattaya", "Chonburi", "Rayong"],
        "Northern": ["Chiang Mai", "Chiang Rai"],
        "Southern": ["Phuket", "Hat Yai", "Koh Samui"],
    },
    "Vietnam": {
        "Ho Chi Minh City": ["Ho Chi Minh City", "District 1", "District 2", "District 7", "Thu Duc"],
        "Hanoi": ["Hanoi", "Ba Dinh", "Hoan Kiem", "Cau Giay"],
        "Da Nang": ["Da Nang"],
        "Hai Phong": ["Hai Phong"],
        "Binh Duong": ["Thu Dau Mot", "Di An"],
    },
    "Philippines": {
        "Metro Manila": ["Manila", "Makati", "Taguig (BGC)", "Quezon City", "Pasig", "Mandaluyong"],
        "Central Visayas": ["Cebu City", "Mandaue", "Lapu-Lapu"],
        "Davao Region": ["Davao City"],
        "Calabarzon": ["Calamba", "Santa Rosa", "Antipolo"],
    },
    "Netherlands": {
        "North Holland": ["Amsterdam", "Haarlem", "Hilversum", "Amstelveen"],
        "South Holland": ["Rotterdam", "The Hague", "Leiden", "Delft"],
        "Utrecht": ["Utrecht", "Amersfoort"],
        "North Brabant": ["Eindhoven", "Tilburg", "Breda", "'s-Hertogenbosch"],
        "Gelderland": ["Arnhem", "Nijmegen", "Apeldoorn"],
        "Overijssel": ["Enschede", "Zwolle"],
        "Groningen": ["Groningen"],
    },
    "Switzerland": {
        "Zurich": ["Zurich", "Winterthur"],
        "Geneva": ["Geneva", "Vernier"],
        "Vaud": ["Lausanne", "Yverdon-les-Bains", "Montreux"],
        "Basel-City": ["Basel"],
        "Bern": ["Bern", "Biel/Bienne", "Thun"],
        "Lucerne": ["Lucerne"],
        "Zug": ["Zug", "Baar"],
        "St. Gallen": ["St. Gallen"],
        "Ticino": ["Lugano", "Bellinzona", "Locarno"],
    },
    "Italy": {
        "Lombardy": ["Milan", "Brescia", "Monza", "Bergamo", "Como"],
        "Lazio": ["Rome", "Latina", "Guidonia Montecelio"],
        "Veneto": ["Venice", "Verona", "Padua", "Vicenza", "Treviso"],
        "Piedmont": ["Turin", "Novara", "Alessandria"],
        "Emilia-Romagna": ["Bologna", "Modena", "Parma", "Reggio Emilia", "Ravenna", "Rimini"],
        "Tuscany": ["Florence", "Prato", "Livorno", "Pisa"],
        "Campania": ["Naples", "Salerno", "Giugliano in Campania"],
        "Sicily": ["Palermo", "Catania", "Messina"],
        "Liguria": ["Genoa", "La Spezia"],
        "Apulia": ["Bari", "Taranto", "Foggia"],
    },
    "Spain": {
        "Community of Madrid": ["Madrid", "Alcalá de Henares", "Fuenlabrada", "Leganés", "Getafe"],
        "Catalonia": ["Barcelona", "L'Hospitalet de Llobregat", "Badalona", "Terrassa", "Sabadell"],
        "Andalusia": ["Seville", "Málaga", "Córdoba", "Granada", "Marbella"],
        "Valencian Community": ["Valencia", "Alicante", "Elche", "Castellón de la Plana"],
        "Basque Country": ["Bilbao", "Vitoria-Gasteiz", "San Sebastián"],
        "Galicia": ["Vigo", "A Coruña", "Santiago de Compostela"],
        "Balearic Islands": ["Palma de Mallorca", "Ibiza"],
        "Canary Islands": ["Las Palmas", "Santa Cruz de Tenerife"],
    },
    "Belgium": {
        "Brussels-Capital": ["Brussels", "Ixelles", "Schaerbeek", "Anderlecht"],
        "Flanders": ["Antwerp", "Ghent", "Bruges", "Leuven", "Mechelen"],
        "Wallonia": ["Liège", "Charleroi", "Namur", "Mons"],
    },
    "Ireland": {
        "Leinster": ["Dublin", "Dún Laoghaire", "Swords", "Kilkenny", "Drogheda"],
        "Munster": ["Cork", "Limerick", "Waterford"],
        "Connacht": ["Galway", "Sligo"],
    },
    "Sweden": {
        "Stockholm County": ["Stockholm", "Solna", "Kista", "Södertälje"],
        "Västra Götaland": ["Gothenburg", "Borås", "Mölndal"],
        "Skåne": ["Malmö", "Lund", "Helsingborg"],
        "Uppsala": ["Uppsala"],
        "Östergötland": ["Linköping", "Norrköping"],
    },
    "Norway": {
        "Oslo Region": ["Oslo", "Bærum", "Asker", "Lillestrøm"],
        "Vestland": ["Bergen"],
        "Rogaland": ["Stavanger", "Sandnes"],
        "Trøndelag": ["Trondheim"],
        "Agder": ["Kristiansand"],
        "Troms og Finnmark": ["Tromsø"],
    },
    "Denmark": {
        "Capital Region": ["Copenhagen", "Frederiksberg", "Helsingør"],
        "Central Denmark": ["Aarhus", "Randers", "Silkeborg"],
        "Region of Southern Denmark": ["Odense", "Esbjerg", "Kolding", "Vejle"],
        "North Denmark": ["Aalborg"],
    },
    "Finland": {
        "Uusimaa": ["Helsinki", "Espoo", "Vantaa", "Kauniainen"],
        "Pirkanmaa": ["Tampere"],
        "Southwest Finland": ["Turku"],
        "North Ostrobothnia": ["Oulu"],
        "Central Finland": ["Jyväskylä"],
    },
    "Poland": {
        "Masovian": ["Warsaw", "Radom", "Płock"],
        "Lesser Poland": ["Kraków", "Tarnów"],
        "Lower Silesian": ["Wrocław", "Wałbrzych", "Legnica"],
        "Silesian": ["Katowice", "Gliwice", "Sosnowiec", "Częstochowa"],
        "Greater Poland": ["Poznań", "Kalisz"],
        "Pomeranian": ["Gdańsk", "Gdynia", "Sopot"],
        "Łódź Voivodeship": ["Łódź"],
    },
    "Austria": {
        "Vienna": ["Vienna"],
        "Lower Austria": ["Sankt Pölten", "Wiener Neustadt"],
        "Upper Austria": ["Linz", "Wels", "Steyr"],
        "Styria": ["Graz", "Leoben"],
        "Salzburg": ["Salzburg"],
        "Tyrol": ["Innsbruck"],
        "Carinthia": ["Klagenfurt", "Villach"],
        "Vorarlberg": ["Bregenz", "Dornbirn"],
    },
    "Portugal": {
        "Lisbon Region": ["Lisbon", "Sintra", "Cascais", "Amadora", "Loures"],
        "Norte": ["Porto", "Vila Nova de Gaia", "Braga", "Guimarães"],
        "Centro": ["Coimbra", "Aveiro", "Leiria"],
        "Algarve": ["Faro", "Portimão", "Loulé"],
        "Madeira": ["Funchal"],
    },
    "South Africa": {
        "Gauteng": ["Johannesburg", "Pretoria", "Sandton", "Midrand", "Centurion"],
        "Western Cape": ["Cape Town", "Stellenbosch", "George"],
        "KwaZulu-Natal": ["Durban", "Pietermaritzburg", "Umhlanga"],
        "Eastern Cape": ["Gqeberha (Port Elizabeth)", "East London"],
        "Free State": ["Bloemfontein"],
    },
    "Nigeria": {
        "Lagos State": ["Lagos", "Ikeja", "Victoria Island", "Lekki", "Surulere"],
        "Abuja Federal Capital": ["Abuja", "Garki", "Wuse", "Maitama"],
        "Rivers State": ["Port Harcourt"],
        "Oyo State": ["Ibadan"],
        "Kano State": ["Kano"],
    },
    "Kenya": {
        "Nairobi County": ["Nairobi", "Westlands", "Kilimani", "Upper Hill"],
        "Mombasa County": ["Mombasa"],
        "Kisumu County": ["Kisumu"],
        "Nakuru County": ["Nakuru"],
        "Uasin Gishu": ["Eldoret"],
    },
    "Brazil": {
        "São Paulo": ["São Paulo", "Campinas", "Guarulhos", "São Bernardo do Campo", "Santo André", "Santos", "Ribeirão Preto"],
        "Rio de Janeiro": ["Rio de Janeiro", "Niterói", "Duque de Caxias", "Nova Iguaçu"],
        "Minas Gerais": ["Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora"],
        "Paraná": ["Curitiba", "Londrina", "Maringá"],
        "Rio Grande do Sul": ["Porto Alegre", "Caxias do Sul", "Canoas"],
        "Bahia": ["Salvador", "Feira de Santana"],
        "Santa Catarina": ["Florianópolis", "Joinville", "Blumenau"],
        "Federal District": ["Brasília"],
    },
    "Mexico": {
        "Mexico City": ["Mexico City", "Polanco", "Santa Fe", "Condesa", "Coyoacán"],
        "Nuevo León": ["Monterrey", "San Pedro Garza García", "Guadalupe", "Apodaca"],
        "Jalisco": ["Guadalajara", "Zapopan", "Tlaquepaque"],
        "State of Mexico": ["Naucalpan", "Tlalnepantla", "Toluca", "Ecatepec"],
        "Querétaro": ["Querétaro", "San Juan del Río"],
        "Puebla": ["Puebla"],
        "Guanajuato": ["León", "Irapuato", "Celaya"],
        "Quintana Roo": ["Cancún", "Playa del Carmen"],
    },
    "Turkey": {
        "Istanbul": ["Istanbul", "Kadıköy", "Beşiktaş", "Şişli", "Üsküdar", "Bakırköy"],
        "Ankara": ["Ankara", "Çankaya", "Keçiören", "Yenimahalle"],
        "Izmir": ["Izmir", "Konak", "Karşıyaka", "Bornova"],
        "Bursa": ["Bursa", "Nilüfer", "Osmangazi"],
        "Antalya": ["Antalya", "Muratpaşa", "Alanya"],
        "Adana": ["Adana", "Seyhan"],
        "Gaziantep": ["Gaziantep", "Şahinbey"],
        "Kocaeli": ["Gebze", "İzmit"],
    },
    "Jordan": {
        "Amman Governorate": ["Amman", "Abdali", "Jabal Amman", "Shmeisani", "Sweifieh"],
        "Zarqa Governorate": ["Zarqa", "Russeifa"],
        "Irbid Governorate": ["Irbid"],
        "Aqaba Governorate": ["Aqaba"],
    },
    "Lebanon": {
        "Beirut Governorate": ["Beirut", "Achrafieh", "Hamra", "Verdun"],
        "Mount Lebanon": ["Jounieh", "Metn", "Baabda", "Aley"],
        "North Governorate": ["Tripoli"],
        "South Governorate": ["Sidon", "Tyre"],
    },
    "New Zealand": {
        "Auckland Region": ["Auckland", "Manukau", "North Shore", "Waitakere"],
        "Wellington Region": ["Wellington", "Lower Hutt", "Porirua"],
        "Canterbury": ["Christchurch"],
        "Waikato": ["Hamilton"],
        "Bay of Plenty": ["Tauranga", "Rotorua"],
        "Otago": ["Dunedin", "Queenstown"],
    },
    "Pakistan": {
        "Sindh": ["Karachi", "Hyderabad", "Sukkur"],
        "Punjab": ["Lahore", "Faisalabad", "Rawalpindi", "Multan", "Gujranwala", "Sialkot"],
        "Islamabad Capital Territory": ["Islamabad"],
        "Khyber Pakhtunkhwa": ["Peshawar", "Mardan", "Abbottabad"],
        "Balochistan": ["Quetta"],
    },
    "Morocco": {
        "Casablanca-Settat": ["Casablanca", "Mohammedia", "El Jadida"],
        "Rabat-Salé-Kénitra": ["Rabat", "Salé", "Kénitra"],
        "Tanger-Tetouan-Al Hoceima": ["Tangier", "Tétouan"],
        "Marrakech-Safi": ["Marrakech", "Safi"],
        "Fès-Meknès": ["Fes", "Meknes"],
        "Souss-Massa": ["Agadir"],
    },
    "Czech Republic": {
        "Prague": ["Prague"],
        "South Moravian": ["Brno"],
        "Moravian-Silesian": ["Ostrava"],
        "Plzeň Region": ["Plzeň"],
    },
    "Romania": {
        "Bucharest-Ilfov": ["Bucharest", "Voluntari", "Otopeni"],
        "Cluj": ["Cluj-Napoca"],
        "Timiș": ["Timișoara"],
        "Iași": ["Iași"],
        "Brașov": ["Brașov"],
        "Constanța": ["Constanța"],
    },
    "Hungary": {
        "Central Hungary": ["Budapest"],
        "Northern Great Plain": ["Debrecen"],
        "Southern Great Plain": ["Szeged"],
        "Northern Hungary": ["Miskolc"],
        "Western Transdanubia": ["Győr"],
    },
    "Greece": {
        "Attica": ["Athens", "Piraeus", "Glyfada", "Marousi"],
        "Central Macedonia": ["Thessaloniki"],
        "Crete": ["Heraklion", "Chania"],
        "Western Greece": ["Patras"],
    },
    "Argentina": {
        "Buenos Aires Autonomous City": ["Buenos Aires", "Palermo", "Puerto Madero", "Recoleta"],
        "Buenos Aires Province": ["La Plata", "Mar del Plata", "Bahía Blanca"],
        "Córdoba": ["Córdoba", "Villa Carlos Paz"],
        "Santa Fe": ["Rosario", "Santa Fe"],
        "Mendoza": ["Mendoza"],
    },
    "Chile": {
        "Santiago Metropolitan": ["Santiago", "Las Condes", "Providencia", "Vitacura"],
        "Valparaíso": ["Valparaíso", "Viña del Mar"],
        "Biobío": ["Concepción"],
        "Antofagasta": ["Antofagasta"],
    },
    "Colombia": {
        "Bogotá Capital District": ["Bogotá", "Chapinero", "Usaquén", "Suba"],
        "Antioquia": ["Medellín", "Envigado", "Bello", "Itagüí"],
        "Valle del Cauca": ["Cali"],
        "Atlántico": ["Barranquilla"],
        "Santander": ["Bucaramanga"],
        "Bolívar": ["Cartagena"],
    },
    "Peru": {
        "Lima Province": ["Lima", "Miraflores", "San Isidro", "Surco"],
        "Arequipa": ["Arequipa"],
        "La Libertad": ["Trujillo"],
        "Cusco": ["Cusco"],
    },
    "Bangladesh": {
        "Dhaka Division": ["Dhaka", "Gulshan", "Banani", "Uttara", "Gazipur"],
        "Chittagong Division": ["Chittagong", "Cox's Bazar"],
        "Sylhet Division": ["Sylhet"],
    },
    "Sri Lanka": {
        "Western Province": ["Colombo", "Dehiwala", "Negombo"],
        "Central Province": ["Kandy"],
        "Southern Province": ["Galle"],
    },
    "Iraq": {
        "Baghdad Governorate": ["Baghdad", "Karrada", "Mansour"],
        "Basra Governorate": ["Basra"],
        "Erbil Governorate": ["Erbil", "Ankawa"],
        "Sulaymaniyah Governorate": ["Sulaymaniyah"],
    },
    "Algeria": {
        "Algiers Province": ["Algiers", "Bab Ezzouar", "Hydra"],
        "Oran Province": ["Oran"],
        "Constantine Province": ["Constantine"],
    },
    "Tunisia": {
        "Tunis Governorate": ["Tunis", "La Marsa", "Carthage"],
        "Sfax Governorate": ["Sfax"],
        "Sousse Governorate": ["Sousse"],
    },
    "Ghana": {
        "Greater Accra": ["Accra", "Tema"],
        "Ashanti": ["Kumasi"],
    },
    "Ethiopia": {
        "Addis Ababa": ["Addis Ababa", "Bole", "Kirkos"],
    },
    "Rwanda": {
        "Kigali": ["Kigali", "Nyarugenge", "Gasabo", "Kicukiro"],
    },
    "Mauritius": {
        "Port Louis": ["Port Louis"],
        "Plaines Wilhems": ["Ebene Cybercity", "Beau Bassin-Rose Hill", "Curepipe"],
    },
    "Monaco": {
        "Monaco": ["Monaco-Ville", "Monte Carlo", "La Condamine", "Fontvieille"],
    },
    "Luxembourg": {
        "Luxembourg Canton": ["Luxembourg City", "Kirchberg"],
        "Esch-sur-Alzette": ["Esch-sur-Alzette"],
    },
    "Cyprus": {
        "Nicosia District": ["Nicosia", "Strovolos"],
        "Limassol District": ["Limassol"],
        "Larnaca District": ["Larnaca"],
        "Paphos District": ["Paphos"],
    },
    "Malta": {
        "Southern Harbour": ["Valletta", "Birgu"],
        "Northern Harbour": ["Sliema", "St. Julian's", "Gzira", "Birkirkara"],
    },
    "Iceland": {
        "Capital Region": ["Reykjavík", "Kópavogur", "Hafnarfjörður"],
    },
    "Estonia": {
        "Harju County": ["Tallinn"],
        "Tartu County": ["Tartu"],
    },
    "Latvia": {
        "Riga Region": ["Riga", "Jūrmala"],
    },
    "Lithuania": {
        "Vilnius County": ["Vilnius"],
        "Kaunas County": ["Kaunas"],
        "Klaipėda County": ["Klaipėda"],
    },
    "Slovakia": {
        "Bratislava Region": ["Bratislava"],
        "Košice Region": ["Košice"],
    },
    "Slovenia": {
        "Central Slovenia": ["Ljubljana"],
        "Drava": ["Maribor"],
    },
    "Croatia": {
        "City of Zagreb": ["Zagreb"],
        "Split-Dalmatia": ["Split"],
        "Primorje-Gorski Kotar": ["Rijeka"],
    },
    "Bulgaria": {
        "Sofia City": ["Sofia"],
        "Plovdiv": ["Plovdiv"],
        "Varna": ["Varna"],
    },
    "Serbia": {
        "Belgrade": ["Belgrade", "Novi Beograd"],
        "South Bačka": ["Novi Sad"],
        "Nišava": ["Niš"],
    },
    "Kazakhstan": {
        "Almaty": ["Almaty"],
        "Astana": ["Astana"],
        "Shymkent": ["Shymkent"],
    },
    "Uzbekistan": {
        "Tashkent": ["Tashkent"],
        "Samarkand": ["Samarkand"],
    },
    "Azerbaijan": {
        "Baku": ["Baku"],
        "Ganja": ["Ganja"],
    },
    "Georgia": {
        "Tbilisi": ["Tbilisi"],
        "Adjara": ["Batumi"],
    },
    "Armenia": {
        "Yerevan": ["Yerevan"],
    },
}

# Add standard entry for any other global countries so every nation exists
STANDARD_GLOBAL_COUNTRIES = [
    "Afghanistan", "Albania", "Andorra", "Angola", "Antigua and Barbuda",
    "Bahamas", "Barbados", "Belarus", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brunei", "Burkina Faso",
    "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Central African Republic",
    "Chad", "Comoros", "Congo (Brazzaville)", "Congo (Kinshasa)", "Costa Rica",
    "Côte d'Ivoire", "Cuba", "Djibouti", "Dominica", "Dominican Republic",
    "Ecuador", "El Salvador", "Equatorial Guinea", "Eritrea", "Eswatini",
    "Fiji", "Gabon", "Gambia", "Grenada", "Guatemala", "Guinea",
    "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Iran", "Jamaica",
    "Kiribati", "Kosovo", "Kyrgyzstan", "Laos", "Lesotho", "Liberia",
    "Libya", "Liechtenstein", "Madagascar", "Malawi", "Maldives", "Mali",
    "Marshall Islands", "Mauritania", "Micronesia", "Moldova", "Mongolia",
    "Montenegro", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal",
    "Nicaragua", "Niger", "North Macedonia", "Palau", "Palestine", "Panama",
    "Papua New Guinea", "Paraguay", "Saint Kitts and Nevis", "Saint Lucia",
    "Saint Vincent and the Grenadines", "Samoa", "San Marino", "São Tomé and Príncipe",
    "Senegal", "Seychelles", "Sierra Leone", "Solomon Islands", "Somalia",
    "South Sudan", "Sudan", "Suriname", "Syria", "Tajikistan", "Tanzania",
    "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Turkmenistan",
    "Tuvalu", "Uganda", "Uruguay", "Vanuatu", "Vatican City", "Venezuela",
    "Yemen", "Zambia", "Zimbabwe"
]

# Ensure every country has an entry
for _c in STANDARD_GLOBAL_COUNTRIES:
    if _c not in GEO_HIERARCHY:
        GEO_HIERARCHY[_c] = {
            "National": [_c]
        }


def get_all_countries() -> list[str]:
    """Returns sorted list of all countries available."""
    return sorted(GEO_HIERARCHY.keys())


def get_states_for_countries(countries: list[str]) -> list[dict[str, Any]]:
    """
    Returns a list of state objects filtered by the given countries:
    [ { "country": "United States", "state": "California", "cities_count": 13 }, ... ]
    """
    results: list[dict[str, Any]] = []
    if not countries:
        return results

    clean_countries = {c.strip().lower() for c in countries if c.strip()}
    is_select_all = "all" in clean_countries

    for country, states in GEO_HIERARCHY.items():
        if is_select_all or country.lower() in clean_countries:
            for state_name, cities in states.items():
                results.append({
                    "country": country,
                    "state": state_name,
                    "full_label": f"{state_name} ({country})",
                    "cities_count": len(cities),
                })
    return results


def get_cities_for_selection(
    countries: list[str] | None = None,
    states: list[str] | None = None,
) -> list[dict[str, str]]:
    """
    Returns list of city objects filtered by chosen countries and optionally chosen states:
    [ { "city": "Riyadh", "state": "Riyadh Province", "country": "Saudi Arabia", "display": "Riyadh, Saudi Arabia" }, ... ]
    """
    results: list[dict[str, str]] = []
    clean_countries = {c.strip().lower() for c in (countries or []) if c.strip()}
    clean_states = {s.strip().lower() for s in (states or []) if s.strip()}

    filter_country = bool(clean_countries) and "all" not in clean_countries
    filter_state = bool(clean_states) and "all" not in clean_states

    for country, state_map in GEO_HIERARCHY.items():
        if filter_country and country.lower() not in clean_countries:
            continue
        for state_name, cities in state_map.items():
            # Check if this state is selected (either plain state name or "State (Country)")
            state_lower = state_name.lower()
            state_with_country = f"{state_lower} ({country.lower()})"
            if filter_state and state_lower not in clean_states and state_with_country not in clean_states:
                continue
            for city in cities:
                results.append({
                    "city": city,
                    "state": state_name,
                    "country": country,
                    "display": f"{city}, {country}" if state_name in ("National", city) else f"{city}, {state_name}, {country}",
                })
    return results


def get_full_hierarchy() -> dict[str, dict[str, list[str]]]:
    """Returns the full hierarchy dict."""
    return GEO_HIERARCHY


def resolve_location_details(loc: str, fallback_country: str = "") -> tuple[str, str, str]:
    """
    Given a location string such as:
      - "Miami, Florida, United States"
      - "Riyadh, Saudi Arabia"
      - "London"
    Returns (city, country, display_name).
    """
    loc_clean = (loc or "").strip()
    if not loc_clean:
        return "New York", fallback_country or "United States", "New York"

    parts = [p.strip() for p in loc_clean.split(",") if p.strip()]
    if len(parts) >= 3:
        # e.g. "Miami", "Florida", "United States"
        city = parts[0]
        country = parts[-1]
        return city, country, loc_clean
    elif len(parts) == 2:
        city = parts[0]
        country_or_state = parts[1]
        # check if 2nd part is a known country
        for c in GEO_HIERARCHY:
            if c.lower() == country_or_state.lower():
                return city, c, loc_clean
        # otherwise 2nd part might be state
        return city, fallback_country or "United States", loc_clean
    else:
        city = loc_clean
        # Look up city in GEO_HIERARCHY if fallback_country not specified
        if not fallback_country:
            for c, states in GEO_HIERARCHY.items():
                for s, cities in states.items():
                    if any(c_name.lower() == city.lower() for c_name in cities):
                        return city, c, f"{city}, {c}"
        return city, fallback_country or "United States", city

