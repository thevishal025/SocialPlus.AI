/**
 * SocialPlus.ai — How to Use Multilingual Guide
 * Supports English and all 22 Scheduled Languages of India.
 * Translates ONLY the How to Use section when a language is selected.
 */

const HOW_TO_USE_LANGUAGES = {
  en: {
    name: "English",
    title: "How to Use SocialPlus.ai",
    subtitle: "A beginner-friendly step-by-step guide to extract and analyze comments across YouTube, Meta, and E-commerce.",
    yt_title: "YouTube Analyzer",
    yt_desc: "Analyze audience feedback, sentiment, and sentiment trends from YouTube video comments.",
    yt_step1: "Select YouTube Analyzer from the home screen.",
    yt_step2: "Paste the YouTube Video URL (e.g., https://www.youtube.com/watch?v=... or Shorts link).",
    yt_step3: "Choose your Comment Quality / Quantity limit (100, 500, 1000+, or All Available).",
    yt_step4: "Click 'Fetch Comments' to launch the AI analysis and inspect sentiment, emotions, and intent.",
    meta_title: "Meta Analyzer (Instagram & Facebook)",
    meta_desc: "Understand audience reactions on Instagram posts, reels, and Facebook public pages.",
    meta_step1: "Select Meta Analyzer from the home screen and choose either Instagram or Facebook.",
    meta_step2: "Select your input mode: official API, public inspection, or manual file upload.",
    meta_step3: "Paste the post or reel link and select your comment limit.",
    meta_step4: "Click 'Fetch & Analyze' to see instant sentiment distribution, top emojis, and toxicity flags.",
    ecom_title: "E-Commerce Analyzer",
    ecom_desc: "Extract verified customer reviews and specifications from Amazon, Flipkart, Meesho, Jio/AJIO, and Myntra.",
    ecom_step1: "Select E-commerce Analyzer from the home screen.",
    ecom_step2: "Paste any product listing URL from Amazon, Flipkart, Meesho, AJIO, or Myntra.",
    ecom_step3: "SocialPlus.ai automatically identifies the platform and product identifiers.",
    ecom_step4: "Click 'Fetch Reviews & Analyze' to collect customer reviews, product aspects, and satisfaction scores.",
    faq_title: "Helpful Tips & Best Practices",
    tip1: "Export Reports: Every analysis can be downloaded as PDF, HTML, Excel (.xlsx), CSV, or JSON.",
    tip2: "History: Access up to 20 past analyses from the History tab at any time without re-fetching.",
    tip3: "File Upload: Have an existing comments export? Use the 'Upload File' tab on any analyzer."
  },
  hi: {
    name: "हिन्दी (Hindi)",
    title: "SocialPlus.ai का उपयोग कैसे करें",
    subtitle: "YouTube, Meta और E-commerce की टिप्पणियों का विश्लेषण करने के लिए सरल मार्गदर्शिका।",
    yt_title: "YouTube विश्लेषक",
    yt_desc: "YouTube वीडियो की टिप्पणियों से दर्शकों की प्रतिक्रिया और भावनाओं का विश्लेषण करें।",
    yt_step1: "होम स्क्रीन से 'YouTube Analyzer' चुनें।",
    yt_step2: "YouTube वीडियो या शॉर्ट्स का लिंक पेस्ट करें।",
    yt_step3: "टिप्पणियों की संख्या (100, 500, 1000+ या सभी) चुनें।",
    yt_step4: "'Fetch Comments' पर क्लिक करें और AI भावना विश्लेषण देखें।",
    meta_title: "Meta विश्लेषक (Instagram और Facebook)",
    meta_desc: "Instagram पोस्ट, रील्स और Facebook पेजों की प्रतिक्रियाओं को समझें।",
    meta_step1: "होम स्क्रीन से 'Meta Analyzer' चुनें और Instagram या Facebook चुनें।",
    meta_step2: "API, पब्लिक या फाइल अपलोड मोड चुनें।",
    meta_step3: "पोस्ट का लिंक दर्ज करें और सीमा तय करें।",
    meta_step4: "'Fetch & Analyze' पर क्लिक करें और विस्तृत रिपोर्ट प्राप्त करें।",
    ecom_title: "ई-कॉमर्स विश्लेषक",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO और Myntra के रिव्यू और विवरण का विश्लेषण।",
    ecom_step1: "होम स्क्रीन से 'E-commerce Analyzer' चुनें।",
    ecom_step2: "समर्थित ई-कॉमर्स साइट से उत्पाद का लिंक पेस्ट करें।",
    ecom_step3: "सिस्टम स्वचालित रूप से प्लेटफॉर्म और उत्पाद की पहचान करेगा।",
    ecom_step4: "'Fetch Reviews & Analyze' पर क्लिक करें और वास्तविक ग्राहक रिव्यू का विश्लेषण देखें।",
    faq_title: "महत्वपूर्ण सुझाव",
    tip1: "रिपोर्ट निर्यात: किसी भी रिपोर्ट को PDF, Excel, CSV या JSON में डाउनलोड करें।",
    tip2: "इतिहास: 'History' टैब से अपने पिछले 20 विश्लेषण कभी भी देखें।",
    tip3: "फाइल अपलोड: अपनी टिप्पणियों की CSV या Excel फाइल सीधे अपलोड कर सकते हैं।"
  },
  bn: {
    name: "বাংলা (Bengali)",
    title: "SocialPlus.ai কীভাবে ব্যবহার করবেন",
    subtitle: "YouTube, Meta এবং E-commerce কমেন্ট বিশ্লেষণের সহজ নির্দেশিকা।",
    yt_title: "YouTube অ্যানালাইজার",
    yt_desc: "ভিডিও কমেন্ট থেকে দর্শকদের মনোভাব এবং প্রতিক্রিয়া বিশ্লেষণ করুন।",
    yt_step1: "হোম স্ক্রিন থেকে 'YouTube Analyzer' নির্বাচন করুন।",
    yt_step2: "YouTube ভিডিও বা শর্টস লিঙ্ক পেস্ট করুন।",
    yt_step3: "কমেন্টের পরিমাণ নির্বাচন করুন (১০০, ৫০০, ১০০০+ বা সব)।",
    yt_step4: "'Fetch Comments' এ ক্লিক করে এআই বিশ্লেষণ দেখুন।",
    meta_title: "Meta অ্যানালাইজার (Instagram ও Facebook)",
    meta_desc: "Instagram ও Facebook পোস্টের প্রতিক্রিয়া এবং সেন্টিমেন্ট জানুন।",
    meta_step1: "Meta Analyzer বেছে নিয়ে Instagram বা Facebook নির্বাচন করুন।",
    meta_step2: "API বা ফাইল আপলোড মোড বেছে নিন।",
    meta_step3: "পোস্টের লিঙ্ক পেস্ট করে কমেন্ট সীমা নির্ধারণ করুন।",
    meta_step4: "'Fetch & Analyze' এ ক্লিক করে ফলাফল দেখুন।",
    ecom_title: "ই-কমার্স অ্যানালাইজার",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO এবং Myntra রিভিউ বিশ্লেষণ।",
    ecom_step1: "হোম পেজ থেকে 'E-commerce Analyzer' বেছে নিন।",
    ecom_step2: "যেকোনো সমর্থিত পণ্যের লিঙ্ক পেস্ট করুন।",
    ecom_step3: "সিস্টেম স্বয়ংক্রিয়ভাবে প্ল্যাটফর্ম সনাক্ত করবে।",
    ecom_step4: "'Fetch Reviews & Analyze' এ ক্লিক করে গ্রাহক মতামত বিশ্লেষণ দেখুন।",
    faq_title: "প্রয়োজনীয় টিপস",
    tip1: "রিপোর্ট এক্সপোর্ট: PDF, Excel, CSV বা JSON আকারে ডাউনলোড করুন।",
    tip2: "হিস্ট্রি: অতীতের ২০টি বিশ্লেষণ হিস্ট্রি ট্যাবে সংরক্ষিত থাকে।",
    tip3: "ফাইল আপলোড: নিজস্ব CSV বা Excel ফাইল আপলোড করে বিশ্লেষণ করতে পারেন।"
  },
  te: {
    name: "తెలుగు (Telugu)",
    title: "SocialPlus.ai ను ఎలా ఉపయోగించాలి",
    subtitle: "YouTube, Meta మరియు ఈ-కామర్స్ కామెంట్లను విశ్లేషించడానికి సులభమైన గైడ్.",
    yt_title: "YouTube ఎనలైజర్",
    yt_desc: "వీడియో వ్యాఖ్యల నుండి ప్రేక్షకుల అభిప్రాయాలను మరియు భావోద్వేగాలను విశ్లేషించండి.",
    yt_step1: "హోమ్ స్క్రీన్ నుండి 'YouTube Analyzer' ఎంచుకోండి.",
    yt_step2: "YouTube వీడియో లేదా షార్ట్స్ లింక్‌ను పేస్ట్ చేయండి.",
    yt_step3: "కామెంట్ల పరిమాణాన్ని (100, 500, 1000+) ఎంచుకోండి.",
    yt_step4: "'Fetch Comments' క్లిక్ చేసి AI విశ్లేషణను వీక్షించండి.",
    meta_title: "Meta ఎనలైజర్ (Instagram & Facebook)",
    meta_desc: "Instagram, Facebook పోస్టుల నుండి కామెంట్ ఇంటెలిజెన్స్ పొందండి.",
    meta_step1: "Meta Analyzer ఎంచుకుని Instagram లేదా Facebook ఎంచుకోండి.",
    meta_step2: "API లేదా ఫైల్ అప్‌లోడ్ మోడ్ ఎంచుకోండి.",
    meta_step3: "పోస్ట్ లింక్ నమోదు చేసి కామెంట్ పరిమితిని ఎంచుకోండి.",
    meta_step4: "'Fetch & Analyze' క్లిక్ చేసి నివేదికను పొందండి.",
    ecom_title: "ఈ-కామర్స్ ఎనలైజర్",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO మరియు Myntra రివ్యూల విశ్లేషణ.",
    ecom_step1: "హోమ్ నుండి 'E-commerce Analyzer' ఎంచుకోండి.",
    ecom_step2: "ఉత్పత్తి లింక్‌ను పేస్ట్ చేయండి.",
    ecom_step3: "సిస్టమ్ స్వయంచాలకంగా ప్లాట్‌ఫారమ్‌ను గుర్తిస్తుంది.",
    ecom_step4: "'Fetch Reviews & Analyze' క్లిక్ చేసి కస్టమర్ రివ్యూల అంతర్దృష్టులను చూడండి.",
    faq_title: "ఉపయోగకరమైన చిట్కాలు",
    tip1: "ఎగుమతి: రిపోర్టులను PDF, Excel, CSV లేదా JSON లో డౌన్‌లోడ్ చేసుకోండి.",
    tip2: "చరిత్ర: గత 20 విశ్లేషణలను 'History' ట్యాబ్‌లో చూడవచ్చు.",
    tip3: "ఫైల్ అప్‌లోడ్: మీ వద్ద ఉన్న CSV లేదా Excel ఫైల్‌ను అప్‌లోడ్ చేయవచ్చు."
  },
  mr: {
    name: "मराठी (Marathi)",
    title: "SocialPlus.ai कसे वापरावे",
    subtitle: "YouTube, Meta आणि ई-कॉमर्स टिप्पण्यांचे विश्लेषण करण्यासाठी सोपे मार्गदर्शक.",
    yt_title: "YouTube विश्लेषक",
    yt_desc: "व्हिडिओ टिप्पण्यांमधून प्रेक्षकांच्या प्रतिक्रियांचे अचूक विश्लेषण करा.",
    yt_step1: "मुख्य पृष्ठावरून 'YouTube Analyzer' निवडा.",
    yt_step2: "YouTube व्हिडिओ किंवा शॉर्ट्सची लिंक पेस्ट करा.",
    yt_step3: "टिप्पण्यांची संख्या मर्यादा (100, 500, 1000+) निवडा.",
    yt_step4: "'Fetch Comments' वर क्लिक करून निकाल पहा.",
    meta_title: "Meta विश्लेषक (Instagram व Facebook)",
    meta_desc: "Instagram व Facebook पोस्ट्सवरील प्रतिक्रिया जाणून घ्या.",
    meta_step1: "Meta Analyzer निवडून Instagram किंवा Facebook निवडा.",
    meta_step2: "API किंवा फाइल अपलोड पर्याय निवडा.",
    meta_step3: "पोस्टची लिंक प्रविष्ट करा.",
    meta_step4: "'Fetch & Analyze' वर क्लिक करून सविस्तर अहवाल पहा.",
    ecom_title: "ई-कॉमर्स विश्लेषक",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO आणि Myntra समीक्षण विश्लेषण.",
    ecom_step1: "मुख्य पृष्ठावरून 'E-commerce Analyzer' निवडा.",
    ecom_step2: "उत्पादनाची लिंक पेस्ट करा.",
    ecom_step3: "प्लॅटफॉर्म आपोआप ओळखला जाईल.",
    ecom_step4: "'Fetch Reviews & Analyze' वर क्लिक करून ग्राहकांच्या अभिप्रायाचे विश्लेषण पहा.",
    faq_title: "महत्त्वाच्या टिप्स",
    tip1: "अहवाल डाऊनलोड: अहवाल PDF, Excel, CSV किंवा JSON मध्ये सेव्ह करा.",
    tip2: "इतिहास: मागील 20 विश्लेषणे History टॅबमध्ये उपलब्ध असतात.",
    tip3: "फाइल अपलोड: तुमच्याकडील CSV किंवा Excel फाईल थेट अपलोड करू शकता."
  },
  ta: {
    name: "தமிழ் (Tamil)",
    title: "SocialPlus.ai ஐ எவ்வாறு பயன்படுத்துவது",
    subtitle: "YouTube, Meta மற்றும் E-commerce கருத்துகளை பகுப்பாய்வு செய்வதற்கான எளிய வழிகாட்டி.",
    yt_title: "YouTube பகுப்பாய்வி",
    yt_desc: "YouTube கருத்துகளிலிருந்து பார்வையாளர்களின் கருத்துகள் மற்றும் உணர்வுகளை அறியுங்கள்.",
    yt_step1: "முகப்புப் பக்கத்தில் 'YouTube Analyzer' என்பதைத் தேர்ந்தெடுக்கவும்.",
    yt_step2: "YouTube வீடியோ அல்லது ஷார்ட்ஸ் இணைப்பை ஒட்டவும்.",
    yt_step3: "கருத்துகளின் எண்ணிக்கையைத் தேர்ந்தெடுக்கவும் (100, 500, 1000+).",
    yt_step4: "'Fetch Comments' என்பதைக் கிளிக் செய்து AI முடிவுகளைக் காண்க.",
    meta_title: "Meta பகுப்பாய்வி (Instagram & Facebook)",
    meta_desc: "Instagram மற்றும் Facebook பதிவுகளின் கருத்துகளை பகுப்பாய்வு செய்யுங்கள்.",
    meta_step1: "Meta Analyzer ஐத் தேர்ந்தெடுத்து Instagram அல்லது Facebook ஐத் தேர்வுசெய்க.",
    meta_step2: "API அல்லது கோப்பு பதிவேற்ற முறையைத் தேர்ந்தெடுக்கவும்.",
    meta_step3: "பதிவின் இணைப்பை உள்ளிடவும்.",
    meta_step4: "'Fetch & Analyze' என்பதைக் கிளிக் செய்து விரிவான அறிக்கையைப் பெறவும்.",
    ecom_title: "மின்-வணிக பகுப்பாய்வி",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO, Myntra மதிப்புரைகளின் முழுமையான பகுப்பாய்வு.",
    ecom_step1: "முகப்பிலிருந்து 'E-commerce Analyzer' ஐத் தேர்ந்தெடுக்கவும்.",
    ecom_step2: "ஆதரிக்கப்படும் மின்-வணிக தளத்திலிருந்து தயாரிப்பு இணைப்பை ஒட்டவும்.",
    ecom_step3: "தளம் தானாகவே கண்டறியப்படும்.",
    ecom_step4: "'Fetch Reviews & Analyze' என்பதைக் கிளிக் செய்து வாடிக்கையாளர் உணர்வுகளைக் காணவும்.",
    faq_title: "பயனுள்ள குறிப்புகள்",
    tip1: "அறிக்கைகள்: PDF, Excel, CSV அல்லது JSON வடிவங்களில் பதிவிறக்கம் செய்யலாம்.",
    tip2: "வரலாறு: முந்தைய 20 பகுப்பாய்வுகளை 'History' பகுதியில் பார்க்கலாம்.",
    tip3: "கோப்பு பதிவேற்றம்: ஏற்கனவே உள்ள CSV அல்லது Excel கோப்புகளைப் பதிவேற்றலாம்."
  },
  gu: {
    name: "ગુજરાતી (Gujarati)",
    title: "SocialPlus.ai નો ઉપયોગ કેવી રીતે કરવો",
    subtitle: "YouTube, Meta અને E-commerce ટિપ્પણીઓનું વિશ્લેષણ કરવા માટેની સરળ માર્ગદર્શિકા.",
    yt_title: "YouTube વિશ્લેષક",
    yt_desc: "YouTube વિડીયોની ટિપ્પણીઓમાંથી લોકોનો પ્રતિસાદ અને લાગણીઓનું વિશ્લેષણ કરો.",
    yt_step1: "હોમ સ્ક્રીન પરથી 'YouTube Analyzer' પસંદ કરો.",
    yt_step2: "YouTube વિડીયો અથવા શોર્ટ્સની લિંક પેસ્ટ કરો.",
    yt_step3: "ટિપ્પણીઓની મર્યાદા પસંદ કરો (100, 500, 1000+).",
    yt_step4: "'Fetch Comments' પર ક્લિક કરો અને પરિણામ જુઓ.",
    meta_title: "Meta વિશ્લેષક (Instagram અને Facebook)",
    meta_desc: "Instagram અને Facebook પોસ્ટ્સ પરની ટિપ્પણીઓનું ઊંડાણપૂર્વક વિશ્લેષણ કરો.",
    meta_step1: "Meta Analyzer પસંદ કરો અને Instagram અથવા Facebook પસંદ કરો.",
    meta_step2: "API અથવા ફાઈલ અપલોડ મોડ પસંદ કરો.",
    meta_step3: "પોસ્ટની લિંક દાખલ કરો અને મર્યાદા નક્કી કરો.",
    meta_step4: "'Fetch & Analyze' પર ક્લિક કરીને વિશ્લેષણ જુઓ.",
    ecom_title: "ઈ-કોમર્સ વિશ્લેષક",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO અને Myntra ના રિવ્યૂનું વિશ્લેષણ.",
    ecom_step1: "હોમ પેજ પરથી 'E-commerce Analyzer' પસંદ કરો.",
    ecom_step2: "પ્રોડક્ટની લિંક પેસ્ટ કરો.",
    ecom_step3: "સિસ્ટમ આપમેળે પ્લેટફોર્મ ઓળખી લેશે.",
    ecom_step4: "'Fetch Reviews & Analyze' પર ક્લિક કરીને ગ્રાહક પ્રતિસાદ જુઓ.",
    faq_title: "મહત્વપૂર્ણ ટિપ્સ",
    tip1: "રિપોર્ટ ડાઉનલોડ: PDF, Excel, CSV અથવા JSON ફોર્મેટમાં સેવ કરો.",
    tip2: "ઇતિહાસ: પાછલા 20 વિશ્લેષણો હિસ્ટ્રી ટેબમાં જોઈ શકાય છે.",
    tip3: "ફાઇલ અપલોડ: તમારી પાસે રહેલી CSV કે Excel ફાઈલ સીધી અપલોડ કરી શકો છો."
  },
  kn: {
    name: "ಕನ್ನಡ (Kannada)",
    title: "SocialPlus.ai ಅನ್ನು ಹೇಗೆ ಬಳಸುವುದು",
    subtitle: "YouTube, Meta ಮತ್ತು ಈ-ಕಾಮರ್ಸ್ ಕಾಮೆಂಟ್‌ಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಲು ಸರಳ ಮಾರ್ಗದರ್ಶಿ.",
    yt_title: "YouTube ವಿಶ್ಲೇಷಕ",
    yt_desc: "ವೀಡಿಯೊ ಕಾಮೆಂಟ್‌ಗಳಿಂದ ಪ್ರೇಕ್ಷಕರ ಅಭಿಪ್ರಾಯ ಮತ್ತು ಭಾವನೆಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಿ.",
    yt_step1: "ಮುಖಪುಟದಿಂದ 'YouTube Analyzer' ಆಯ್ಕೆಮಾಡಿ.",
    yt_step2: "YouTube ವೀಡಿಯೊ ಅಥವಾ ಶಾರ್ಟ್ಸ್ ಲಿಂಕ್ ಅನ್ನು ನಮೂದಿಸಿ.",
    yt_step3: "ಕಾಮೆಂಟ್‌ಗಳ ಸಂಖ್ಯೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ (100, 500, 1000+).",
    yt_step4: "'Fetch Comments' ಕ್ಲಿಕ್ ಮಾಡಿ ಮತ್ತು AI ವಿಶ್ಲೇಷಣೆಯನ್ನು ವೀಕ್ಷಿಸಿ.",
    meta_title: "Meta ವಿಶ್ಲೇಷಕ (Instagram & Facebook)",
    meta_desc: "Instagram ಮತ್ತು Facebook ಪೋಸ್ಟ್‌ಗಳ ಪ್ರತಿಕ್ರಿಯೆಗಳನ್ನು ಅರಿಯಿರಿ.",
    meta_step1: "Meta Analyzer ಆಯ್ಕೆಮಾಡಿ ಮತ್ತು Instagram ಅಥವಾ Facebook ಆಯ್ಕೆಮಾಡಿ.",
    meta_step2: "API ಅಥವಾ ಫೈಲ್ ಅಪ್‌ಲೋಡ್ ಮೋಡ್ ಆಯ್ಕೆಮಾಡಿ.",
    meta_step3: "ಪೋಸ್ಟ್ ಲಿಂಕ್ ನಮೂದಿಸಿ ಕಾಮೆಂಟ್ ಮಿತಿ ನಿಗದಿಪಡಿಸಿ.",
    meta_step4: "'Fetch & Analyze' ಕ್ಲಿಕ್ ಮಾಡಿ ವರದಿಯನ್ನು ಪಡೆಯಿರಿ.",
    ecom_title: "ಈ-ಕಾಮರ್ಸ್ ವಿಶ್ಲೇಷಕ",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO ಮತ್ತು Myntra ವಿಮರ್ಶೆಗಳ ವಿಶ್ಲೇಷಣೆ.",
    ecom_step1: "ಮುಖಪುಟದಿಂದ 'E-commerce Analyzer' ಆಯ್ಕೆಮಾಡಿ.",
    ecom_step2: "ಉತ್ಪನ್ನದ ಲಿಂಕ್ ಅನ್ನು ಪೇಸ್ಟ್ ಮಾಡಿ.",
    ecom_step3: "ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ ಅನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಗುರುತಿಸಲಾಗುತ್ತದೆ.",
    ecom_step4: "'Fetch Reviews & Analyze' ಕ್ಲಿಕ್ ಮಾಡಿ ಗ್ರಾಹಕರ ವಿಮರ್ಶೆಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಿ.",
    faq_title: "ಉಪಯುಕ್ತ ಸಲಹೆಗಳು",
    tip1: "ವರದಿ ಡೌನ್‌ಲೋಡ್: PDF, Excel, CSV ಅಥವಾ JSON ರೂಪದಲ್ಲಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿಕೊಳ್ಳಿ.",
    tip2: "ಇತಿಹಾಸ: ಹಿಂದಿನ 20 ವಿಶ್ಲೇಷಣೆಗಳನ್ನು 'History' ಟ್ಯಾಬ್‌ನಲ್ಲಿ ವೀಕ್ಷಿಸಿ.",
    tip3: "ಫೈಲ್ ಅಪ್‌ಲೋಡ್: ನಿಮ್ಮ ಬಳಿಯಿರುವ CSV ಅಥವಾ Excel ಫೈಲ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಬಹುದು."
  },
  ml: {
    name: "മലയാളം (Malayalam)",
    title: "SocialPlus.ai എങ്ങനെ ഉപയോഗിക്കാം",
    subtitle: "YouTube, Meta, E-commerce കമന്റുകൾ വിശകലനം ചെയ്യാനുള്ള ലളിതമായ ഗൈഡ്.",
    yt_title: "YouTube അനലൈസർ",
    yt_desc: "വീഡിയോ കമന്റുകളിൽ നിന്നുള്ള പ്രേക്ഷക പ്രതികരണങ്ങൾ കൃത്യമായി മനസ്സിലാക്കുക.",
    yt_step1: "ഹോം പേജിൽ നിന്ന് 'YouTube Analyzer' തിരഞ്ഞെടുക്കുക.",
    yt_step2: "YouTube വീഡിയോ അല്ലെങ്കിൽ ഷോർട്ട്സ് ലിങ്ക് നൽകുക.",
    yt_step3: "കമന്റുകളുടെ എണ്ണം (100, 500, 1000+) തിരഞ്ഞെടുക്കുക.",
    yt_step4: "'Fetch Comments' ക്ലിക്ക് ചെയ്ത് ഫലങ്ങൾ കാണുക.",
    meta_title: "Meta അനലൈസർ (Instagram & Facebook)",
    meta_desc: "Instagram, Facebook പോസ്റ്റുകളിലെ കമന്റുകൾ വിശകലനം ചെയ്യുക.",
    meta_step1: "Meta Analyzer തിരഞ്ഞെടുത്ത് Instagram അല്ലെങ്കിൽ Facebook തിരഞ്ഞെടുക്കുക.",
    meta_step2: "API അല്ലെങ്കിൽ ഫയൽ അപ്‌ലോഡ് മോഡ് തിരഞ്ഞെടുക്കുക.",
    meta_step3: "പോസ്റ്റ് ലിങ്ക് നൽകുക.",
    meta_step4: "'Fetch & Analyze' ക്ലിക്ക് ചെയ്ത് വിശദമായ റിപ്പോർട്ട് കാണുക.",
    ecom_title: "ഇ-കൊമേഴ്‌സ് അനലൈസർ",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO, Myntra ഉപഭോക്തൃ റിവ്യൂകളുടെ വിശകലനം.",
    ecom_step1: "ഹോമിൽ നിന്ന് 'E-commerce Analyzer' തിരഞ്ഞെടുക്കുക.",
    ecom_step2: "ഉൽപ്പന്നത്തിന്റെ ലിങ്ക് പേസ്റ്റ് ചെയ്യുക.",
    ecom_step3: "പ്ലാറ്റ്ഫോം സ്വയമേവ തിരിച്ചറിയപ്പെടും.",
    ecom_step4: "'Fetch Reviews & Analyze' ക്ലിക്ക് ചെയ്ത് ഉപഭോക്തൃ അഭിപ്രായങ്ങൾ അറിയുക.",
    faq_title: "ഉപകാരപ്രദമായ നിർദ്ദേശങ്ങൾ",
    tip1: "റിപ്പോർട്ടുകൾ: PDF, Excel, CSV അല്ലെങ്കിൽ JSON ആയി ഡൗൺലോഡ് ചെയ്യാം.",
    tip2: "ഹിസ്റ്ററി: മുൻപത്തെ 20 വിശകലനങ്ങൾ 'History' ടാബിൽ സൂക്ഷിക്കുന്നു.",
    tip3: "ഫയൽ അപ്‌ലോഡ്: സ്വന്തം CSV അല്ലെങ്കിൽ Excel ഫയലുകൾ അപ്‌ലോഡ് ചെയ്യാം."
  },
  pa: {
    name: "ਪੰਜਾਬੀ (Punjabi)",
    title: "SocialPlus.ai ਦੀ ਵਰਤੋਂ ਕਿਵੇਂ ਕਰੀਏ",
    subtitle: "YouTube, Meta ਅਤੇ ਈ-ਕਾਮਰਸ ਟਿੱਪਣੀਆਂ ਦਾ ਵਿਸ਼ਲੇਸ਼ਣ ਕਰਨ ਲਈ ਆਸਾਨ ਗਾਈਡ।",
    yt_title: "YouTube ਵਿਸ਼ਲੇਸ਼ਕ",
    yt_desc: "ਵੀਡੀਓ ਟਿੱਪਣੀਆਂ ਤੋਂ ਦਰਸ਼ਕਾਂ ਦੇ ਪ੍ਰਤੀਕਰਮਾਂ ਅਤੇ ਭਾਵਨਾਵਾਂ ਦਾ ਵਿਸ਼ਲੇਸ਼ਣ ਕਰੋ।",
    yt_step1: "ਹੋਮ ਸਕ੍ਰੀਨ ਤੋਂ 'YouTube Analyzer' ਚੁਣੋ।",
    yt_step2: "YouTube ਵੀਡੀਓ ਜਾਂ ਸ਼ਾਰਟਸ ਦਾ ਲਿੰਕ ਪੇਸਟ ਕਰੋ।",
    yt_step3: "ਟਿੱਪਣੀਆਂ ਦੀ ਗਿਣਤੀ ਚੁਣੋ (100, 500, 1000+)।",
    yt_step4: "'Fetch Comments' 'ਤੇ ਕਲਿੱਕ ਕਰੋ ਅਤੇ AI ਵਿਸ਼ਲੇਸ਼ਣ ਦੇਖੋ।",
    meta_title: "Meta ਵਿਸ਼ਲੇਸ਼ਕ (Instagram ਅਤੇ Facebook)",
    meta_desc: "Instagram ਅਤੇ Facebook ਪੋਸਟਾਂ 'ਤੇ ਦਰਸ਼ਕਾਂ ਦੀ ਰਾਏ ਸਮਝੋ।",
    meta_step1: "Meta Analyzer ਚੁਣ ਕੇ Instagram ਜਾਂ Facebook ਚੁਣੋ।",
    meta_step2: "API ਜਾਂ ਫਾਈਲ ਅੱਪਲੋਡ ਮੋਡ ਚੁਣੋ।",
    meta_step3: "ਪੋਸਟ ਲਿੰਕ ਦਰਜ ਕਰੋ।",
    meta_step4: "'Fetch & Analyze' 'ਤੇ ਕਲਿੱਕ ਕਰੋ ਅਤੇ ਨਤੀਜਾ ਵੇਖੋ।",
    ecom_title: "ਈ-ਕਾਮਰਸ ਵਿਸ਼ਲੇਸ਼ਕ",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO ਅਤੇ Myntra ਸਮੀਖਿਆਵਾਂ ਦਾ ਵਿਸ਼ਲੇਸ਼ਣ।",
    ecom_step1: "ਹੋਮ ਸਕ੍ਰੀਨ ਤੋਂ 'E-commerce Analyzer' ਚੁਣੋ।",
    ecom_step2: "ਉਤਪਾਦ ਦਾ ਲਿੰਕ ਪੇਸਟ ਕਰੋ।",
    ecom_step3: "ਸਿਸਟਮ ਆਪਣੇ ਆਪ ਪਲੇਟਫਾਰਮ ਦੀ ਪਛਾਣ ਕਰੇਗਾ।",
    ecom_step4: "'Fetch Reviews & Analyze' 'ਤੇ ਕਲਿੱਕ ਕਰੋ ਅਤੇ ਗਾਹਕਾਂ ਦੀ ਰਾਏ ਜਾਣੋ।",
    faq_title: "ਮਹੱਤਵਪੂਰਨ ਨੁਕਤੇ",
    tip1: "ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ: PDF, Excel, CSV ਜਾਂ JSON ਵਿੱਚ ਸੇਵ ਕਰੋ।",
    tip2: "ਇਤਿਹਾਸ: ਪਿਛਲੇ 20 ਵਿਸ਼ਲੇਸ਼ਣ 'History' ਟੈਬ ਵਿੱਚ ਦੇਖੇ ਜਾ ਸਕਦੇ ਹਨ।",
    tip3: "ਫਾਈਲ ਅੱਪਲੋਡ: ਤੁਹਾਡੇ ਕੋਲ ਮੌਜੂਦ CSV ਜਾਂ Excel ਫਾਈਲ ਅੱਪਲੋਡ ਕਰ ਸਕਦੇ ਹੋ।"
  },
  ur: {
    name: "اردو (Urdu)",
    title: "SocialPlus.ai کا استعمال کیسے کریں",
    subtitle: "یوٹیوب، میٹا اور ای کامرس تبصروں کا تجزیہ کرنے کے لیے آسان گائیڈ۔",
    yt_title: "یوٹیوب اینالائزر",
    yt_desc: "ویڈیو تبصروں سے ناظرین کے تاثرات اور جذبات کا تجزیہ کریں۔",
    yt_step1: "ہوم اسکرین سے 'YouTube Analyzer' کا انتخاب کریں۔",
    yt_step2: "یوٹیوب ویڈیو یا شارٹس کا لنک چسپاں کریں۔",
    yt_step3: "تبصروں کی تعداد (100، 500، 1000+) منتخب کریں۔",
    yt_step4: "'Fetch Comments' پر کلک کریں اور AI تجزیہ دیکھیں۔",
    meta_title: "میٹا اینالائزر (انسٹاگرام اور فیس بک)",
    meta_desc: "انسٹاگرام اور فیس بک پوسٹس پر ناظرین کے تاثرات کو سمجھیں۔",
    meta_step1: "Meta Analyzer منتخب کریں اور انسٹاگرام یا فیس بک چنیں۔",
    meta_step2: "API یا فائل اپ لوڈ کا طریقہ منتخب کریں۔",
    meta_step3: "پوسٹ کا لنک درج کریں اور حد مقرر کریں۔",
    meta_step4: "'Fetch & Analyze' پر کلک کر کے رپورٹ حاصل کریں۔",
    ecom_title: "ای کامرس اینالائزر",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO اور Myntra ریویوز کا تجزیہ۔",
    ecom_step1: "ہوم پیج سے 'E-commerce Analyzer' منتخب کریں۔",
    ecom_step2: "پروڈکٹ کا لنک چسپاں کریں۔",
    ecom_step3: "سسٹم خودکار طریقے سے پلیٹ فارم کو پہچان لے گا۔",
    ecom_step4: "'Fetch Reviews & Analyze' پر کلک کریں اور کسٹمر فیڈ بیک دیکھیں۔",
    faq_title: "اہم نکات",
    tip1: "رپورٹ ڈاؤن لوڈ: PDF، Excel، CSV یا JSON میں محفوظ کریں۔",
    tip2: "تاریخ: پچھلے 20 تجزیے ہسٹری ٹیب میں موجود رہتے ہیں۔",
    tip3: "فائل اپ لوڈ: آپ اپنی CSV یا Excel فائل بھی اپ لوڈ کر سکتے ہیں۔"
  },
  or: {
    name: "ଓଡ଼ିଆ (Odia)",
    title: "SocialPlus.ai କିପରି ବ୍ୟବହାର କରିବେ",
    subtitle: "YouTube, Meta ଏବଂ E-commerce ମତାମତ ବିଶ୍ଳେଷଣ ପାଇଁ ସରଳ ମାର୍ଗଦର୍ଶିକା।",
    yt_title: "YouTube ବିଶ୍ଳେଷକ",
    yt_desc: "ଭିଡିଓ ମନ୍ତବ୍ୟରୁ ଦର୍ଶକଙ୍କ ପ୍ରତିକ୍ରିୟା ଏବଂ ଭାବନା ଜାଣନ୍ତୁ।",
    yt_step1: "ହୋମ୍ ସ୍କ୍ରିନରୁ 'YouTube Analyzer' ଚୟନ କରନ୍ତୁ।",
    yt_step2: "YouTube ଭିଡିଓ ଲିଙ୍କ୍ ପେଷ୍ଟ କରନ୍ତୁ।",
    yt_step3: "ମନ୍ତବ୍ୟ ସଂଖ୍ୟା (100, 500, 1000+) ଚୟନ କରନ୍ତୁ।",
    yt_step4: "'Fetch Comments' ଉପରେ କ୍ଲିକ୍ କରି AI ବିଶ୍ଳେଷଣ ଦେଖନ୍ତୁ।",
    meta_title: "Meta ବିଶ୍ଳେଷକ (Instagram & Facebook)",
    meta_desc: "Instagram ଏବଂ Facebook ପୋଷ୍ଟଗୁଡ଼ିକର ମତାମତ ବିଶ୍ଳେଷଣ କରନ୍ତୁ।",
    meta_step1: "Meta Analyzer ଚୟନ କରି Instagram କିମ୍ବା Facebook ବାଛନ୍ତୁ।",
    meta_step2: "API କିମ୍ବା ଫାଇଲ୍ ଅପଲୋଡ୍ ମୋଡ୍ ବାଛନ୍ତୁ।",
    meta_step3: "ପୋଷ୍ଟ ଲିଙ୍କ୍ ଦିଅନ୍ତୁ।",
    meta_step4: "'Fetch & Analyze' କ୍ଲିକ୍ କରି ଫଳାଫଳ ଦେଖନ୍ତୁ।",
    ecom_title: "ଇ-କମର୍ସ ବିଶ୍ଳେଷକ",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO ଓ Myntra ସମୀକ୍ଷା ବିଶ୍ଳେଷଣ।",
    ecom_step1: "ମୁଖ୍ୟ ପୃଷ୍ଠାରୁ 'E-commerce Analyzer' ବାଛନ୍ତୁ।",
    ecom_step2: "ଉତ୍ପାଦର ଲିଙ୍କ୍ ପେଷ୍ଟ କରନ୍ତୁ।",
    ecom_step3: "ପ୍ଲାଟଫର୍ମ ସ୍ୱୟଂଚାଳିତ ଭାବେ ଚିହ୍ନଟ ହେବ।",
    ecom_step4: "'Fetch Reviews & Analyze' କ୍ଲିକ୍ କରି ଗ୍ରାହକ ମତାମତ ଦେଖନ୍ତୁ।",
    faq_title: "ଗୁରୁତ୍ୱପୂର୍ଣ୍ଣ ସୂଚନା",
    tip1: "ରିପୋର୍ଟ ଡାଉନଲୋଡ୍: PDF, Excel, CSV କିମ୍ବା JSON ରେ ସାଇତି ରଖନ୍ତୁ।",
    tip2: "ଇତିହାସ: ପୂର୍ବର 20 ଟି ବିଶ୍ଳେଷଣ History ଟ୍ୟାବ୍‌ରେ ପାଇପାରିବେ।",
    tip3: "ଫାଇଲ୍ ଅପଲୋଡ୍: CSV କିମ୍ବା Excel ଫାଇଲ୍ ସିଧାସଳଖ ଅପଲୋଡ୍ କରିପାରିବେ।"
  },
  as: {
    name: "অসমীয়া (Assamese)",
    title: "SocialPlus.ai কেনেকৈ ব্যৱহাৰ কৰিব",
    subtitle: "YouTube, Meta আৰু ই-কমাৰ্ছ মন্তব্য বিশ্লেষণৰ সহজ সহায়িকা।",
    yt_title: "YouTube বিশ্লেষক",
    yt_desc: "ভিডিঅ' মন্তব্যৰ পৰা দৰ্শকৰ সঁহাৰি আৰু অনুভূতি বিশ্লেষণ কৰক।",
    yt_step1: "মুখ্য পৃষ্ঠাৰ পৰা 'YouTube Analyzer' বাছক।",
    yt_step2: "YouTube ভিডিঅ'ৰ লিংক পেষ্ট কৰক।",
    yt_step3: "মন্তব্যৰ সীমা নিৰ্ধাৰণ কৰক (১০০, ৫০০, ১০০০+)।",
    yt_step4: "'Fetch Comments' ত ক্লিক কৰি AI ফলাফল চাওক।",
    meta_title: "Meta বিশ্লেষক (Instagram & Facebook)",
    meta_desc: "Instagram আৰু Facebook পোষ্টৰ প্ৰতিক্ৰিয়া বুজি লওক।",
    meta_step1: "Meta Analyzer বাছি লৈ Instagram বা Facebook নিৰ্বাচন কৰক।",
    meta_step2: "API বা ফাইল আপলোড মোড বাছক।",
    meta_step3: "পোষ্টৰ লিংক পেষ্ট কৰক।",
    meta_step4: "'Fetch & Analyze' ত ক্লিক কৰি প্ৰতিবেদন চাওক।",
    ecom_title: "ই-কমাৰ্ছ বিশ্লেষক",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO আৰু Myntra ৰ ৰিভিউ বিশ্লেষণ।",
    ecom_step1: "গৃহ পৃষ্ঠাত 'E-commerce Analyzer' বাছক।",
    ecom_step2: "সামগ্ৰীৰ লিংক পেষ্ট কৰক।",
    ecom_step3: "প্লেটফৰ্ম স্বয়ংক্ৰিয়ভাৱে চিনাক্ত হ'ব।",
    ecom_step4: "'Fetch Reviews & Analyze' ত ক্লিক কৰি গ্ৰাহকৰ মতামত বিশ্লেষণ কৰক।",
    faq_title: "প্ৰয়োজনীয় পৰামৰ্শ",
    tip1: "প্ৰতিবেদন ডাউনলোড: PDF, Excel, CSV বা JSON ত সংৰক্ষণ কৰক।",
    tip2: "ইতিহাস: পুৰণি ২০টা বিশ্লেষণ History টেবত সংৰক্ষিত থাকে।",
    tip3: "ফাইল আপলোড: নিজা CSV বা Excel ফাইল আপলোড কৰিব পাৰি।"
  },
  sa: {
    name: "संस्कृतम् (Sanskrit)",
    title: "SocialPlus.ai कथं प्रयोक्तव्यम्",
    subtitle: "YouTube, Meta तथा E-commerce टिप्पणीनां विश्लेषणाय सरलः मार्गदर्शकः।",
    yt_title: "YouTube विश्लेषकः",
    yt_desc: "दृश्य-टिप्पणीभ्यः दर्शकानां प्रतिक्रियाः भावनाश्च अवगच्छन्तु।",
    yt_step1: "मुख्यपृष्ठात् 'YouTube Analyzer' चिनोतु।",
    yt_step2: "चलचित्रस्य सम्पर्कतन्तुं (URL) प्रविशतु।",
    yt_step3: "टिप्पणीनां संख्यां (१००, ५००, १०००+) चिनोतु।",
    yt_step4: "'Fetch Comments' नुत्वा AI विश्लेषणं पश्यतु।",
    meta_title: "Meta विश्लेषकः (Instagram & Facebook)",
    meta_desc: "Instagram तथा Facebook लेखानां प्रतिक्रियाः परीक्षन्तु।",
    meta_step1: "Meta Analyzer चित्वा Instagram अथवा Facebook चिनोतु।",
    meta_step2: "API अथवा सञ्चिका-आरोपण-विधिं चिनोतु।",
    meta_step3: "सम्पर्कतन्तुं प्रविशतु।",
    meta_step4: "'Fetch & Analyze' नुत्वा विवरणं प्राप्नुवन्तु।",
    ecom_title: "ई-वाणिज्य विश्लेषकः",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO तथा Myntra ग्राहक-समीक्षा-विश्लेषणम्।",
    ecom_step1: "मुख्यात् 'E-commerce Analyzer' चिनोतु।",
    ecom_step2: "उत्पादस्य सम्पर्कतन्तुं प्रविशतु।",
    ecom_step3: "यन्त्रं स्वयं मञ्चं ज्ञास्यति।",
    ecom_step4: "'Fetch Reviews & Analyze' नुत्वा ग्राहक-भावनाः पश्यन्तु।",
    faq_title: "उपयोगिनः उपायाः",
    tip1: "विवरण-रक्षणम्: विवरणं PDF, Excel, CSV अथवा JSON रूपेण स्वीकुर्वन्तु।",
    tip2: "इतिहासः: पूर्वतनानि २० विश्लेषणानि History विभागे लभ्यन्ते।",
    tip3: "सञ्चिका-आरोपणम्: भवतः CSV अथवा Excel सञ्चिकां साक्षात् आरोपयितुं शक्नुवन्ति।"
  },
  ne: {
    name: "नेपाली (Nepali)",
    title: "SocialPlus.ai कसरी प्रयोग गर्ने",
    subtitle: "YouTube, Meta र E-commerce का प्रतिक्रियाहरू विश्लेषण गर्ने सजिलो गाइड।",
    yt_title: "YouTube विश्लेषक",
    yt_desc: "भिडियो प्रतिक्रियाहरूबाट दर्शकहरूको भावना र विचार विश्लेषण गर्नुहोस्।",
    yt_step1: "गृहपृष्ठबाट 'YouTube Analyzer' छान्नुहोस्।",
    yt_step2: "YouTube भिडियो वा सर्ट्सको लिङ्क टाँस्नुहोस्।",
    yt_step3: "टिप्पणीहरूको संख्या (१००, ५००, १०००+) छान्नुहोस्।",
    yt_step4: "'Fetch Comments' मा क्लिक गरेर AI विश्लेषण हेर्नुहोस्।",
    meta_title: "Meta विश्लेषक (Instagram र Facebook)",
    meta_desc: "Instagram र Facebook पोस्टहरूमा आएका प्रतिक्रियाहरूको विश्लेषण।",
    meta_step1: "Meta Analyzer छानेर Instagram वा Facebook रोज्नुहोस्।",
    meta_step2: "API वा फाइल अपलोड विधि रोज्नुहोस्।",
    meta_step3: "पोस्टको लिङ्क हाल्नुहोस्।",
    meta_step4: "'Fetch & Analyze' मा क्लिक गरेर विस्तृत नतिजा पाउनुहोस्।",
    ecom_title: "ई-कमर्स विश्लेषक",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO र Myntra समीक्षा विश्लेषण।",
    ecom_step1: "होमबाट 'E-commerce Analyzer' छान्नुहोस्।",
    ecom_step2: "सामानको लिङ्क टाँस्नुहोस्।",
    ecom_step3: "सिस्टमले आफैं प्लेटफर्म पहिचान गर्नेछ।",
    ecom_step4: "'Fetch Reviews & Analyze' मा क्लिक गरी ग्राहकको धारणा बुझ्नुहोस्।",
    faq_title: "उपयोगी सुझावहरू",
    tip1: "रिपोर्ट डाउनलोड: PDF, Excel, CSV वा JSON मा डाउनलोड गर्न सकिन्छ।",
    tip2: "इतिहास: विगतका २० वटा विश्लेषणहरू History ट्याबमा सुरक्षित रहन्छन्।",
    tip3: "फाइल अपलोड: आफ्नो CSV वा Excel फाइल सिधै अपलोड गर्न सक्नुहुन्छ।"
  },
  sd: {
    name: "سنڌي (Sindhi)",
    title: "SocialPlus.ai ڪيئن استعمال ڪجي",
    subtitle: "YouTube، Meta ۽ E-commerce تبصرن جي تجزيي لاءِ سادو گائيڊ.",
    yt_title: "YouTube اينالائيزر",
    yt_desc: "ويڊيو تبصرن مان ماڻهن جي راءِ ۽ جذبات جو تجزيو ڪريو.",
    yt_step1: "مکيه اسڪرين مان 'YouTube Analyzer' چونڊيو.",
    yt_step2: "YouTube ويڊيو جي لنڪ داخل ڪريو.",
    yt_step3: "تبصرن جو تعداد چونڊيو (100، 500، 1000+).",
    yt_step4: "'Fetch Comments' تي ڪلڪ ڪري AI نتيجا ڏسو.",
    meta_title: "Meta اينالائيزر (Instagram ۽ Facebook)",
    meta_desc: "Instagram ۽ Facebook پوسٽن تي ماڻهن جا تاثرات معلوم ڪريو.",
    meta_step1: "Meta Analyzer چونڊي Instagram يا Facebook تي ڪلڪ ڪريو.",
    meta_step2: "API يا فائل اپلوڊ موڊ چونڊيو.",
    meta_step3: "پوسٽ لنڪ داخل ڪريو.",
    meta_step4: "'Fetch & Analyze' تي ڪلڪ ڪري نتيجا ڏسو.",
    ecom_title: "اي-ڪامرس اينالائيزر",
    ecom_desc: "Amazon، Flipkart، Meesho، Jio/AJIO ۽ Myntra جي تبصرن جو تجزيو.",
    ecom_step1: "مک صفحي مان 'E-commerce Analyzer' چونڊيو.",
    ecom_step2: "سامان جي لنڪ داخل ڪريو.",
    ecom_step3: "سسٽم خودڪار طريقي سان پليٽ فارم سڃاڻي وٺندو.",
    ecom_step4: "'Fetch Reviews & Analyze' تي ڪلڪ ڪري گراهڪن جا رايا ڏسو.",
    faq_title: "ضروري ٽوٽڪا",
    tip1: "رپورٽ ڊائون لوڊ: PDF، Excel، CSV يا JSON ۾ محفوظ ڪريو.",
    tip2: "تاريخ: گذريل 20 تجزيا History ٽئب ۾ موجود رھندا آھن.",
    tip3: "فائل اپلوڊ: پنھنجي CSV يا Excel فائل سڌي اپلوڊ ڪري سگھو ٿا."
  },
  ks: {
    name: "کٲشُر (Kashmiri)",
    title: "SocialPlus.ai کِتھ پٲٹھۍ اِستِعمال کَرُن",
    subtitle: "YouTube، Meta تہٕ E-commerce تبصرن ہُنٛد تجزِیہٕ کَرنُک سَہل طٔریٖقہٕ۔",
    yt_title: "YouTube اینالائزر",
    yt_desc: "ویڈیو تبصرن منٛزٕ لُکن ہٕنٛز راے تہٕ جذبات زانِو۔",
    yt_step1: "ہوم سکرین پؠٹھٕ 'YouTube Analyzer' چُھناو۔",
    yt_step2: "YouTube ویڈیو لنک چسپاں کٔرِو۔",
    yt_step3: "تبصرن ہُنٛد تَعداد چُھناو (100، 500، 1000+)۔",
    yt_step4: "'Fetch Comments' پؠٹھ کِلک کٔرِتھ AI تجزِیہٕ وُچھِو۔",
    meta_title: "Meta اینالائزر (Instagram تہٕ Facebook)",
    meta_desc: "Instagram تہٕ Facebook پوسٹن پؠٹھ عوامُک تاثر معلوم کٔرِو۔",
    meta_step1: "Meta Analyzer منٛزٕ Instagram یا Facebook چُھناو۔",
    meta_step2: "API یا فائل اپلوڈ طریقہٕ منتخب کٔرِو۔",
    meta_step3: "پوسٹ لنک درج کٔرِو۔",
    meta_step4: "'Fetch & Analyze' پؠٹھ کِلک کٔرِو۔",
    ecom_title: "ای-کامرس اینالائزر",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO تہٕ Myntra ریویوز ہُنٛد تجزِیہٕ۔",
    ecom_step1: "ہوم پؠٹھٕ 'E-commerce Analyzer' منتخب کٔرِو۔",
    ecom_step2: "پروڈکٹُک لنک چسپاں کٔرِو۔",
    ecom_step3: "سسٹم پانہٕ پہچانی پلیٹ فارم۔",
    ecom_step4: "'Fetch Reviews & Analyze' پؠٹھ کِلک کٔرِتھ گاہکن ہٕنٛز راے وُچھِو۔",
    faq_title: "اہم نکتہٕ",
    tip1: "رپورٹ ڈاؤنلوڈ: PDF, Excel, CSV یا JSON منٛز مَحفوظ کٔرِو۔",
    tip2: "تاریخ: گُزٔرۍمٕتۍ 20 تجزِیہٕ History ٹیبس منٛز لَبہٕ یِوان۔",
    tip3: "فائل اپلوڈ: تُہۍ ہؠکِو پَنٕنۍ CSV یا Excel فائل سِیدھے اَپلوڈ کٔرِتھ۔"
  },
  mai: {
    name: "मैथिली (Maithili)",
    title: "SocialPlus.ai के उपयोग कोना करी",
    subtitle: "YouTube, Meta आ E-commerce टिप्पणी विश्लेषणक लेल सरल निर्देशिका।",
    yt_title: "YouTube विश्लेषक",
    yt_desc: "वीडियो टिप्पणी सं दर्शक लोकनिक प्रतिक्रिया आ भावुकताक विश्लेषण करू।",
    yt_step1: "होम स्क्रीन सं 'YouTube Analyzer' चुनु।",
    yt_step2: "YouTube वीडियो लिंक पेस्ट करू।",
    yt_step3: "टिप्पणीक संख्या सीमा चुनु (100, 500, 1000+)।",
    yt_step4: "'Fetch Comments' पर क्लिक कऽ AI विश्लेषण देखू।",
    meta_title: "Meta विश्लेषक (Instagram आ Facebook)",
    meta_desc: "Instagram आ Facebook पोस्ट पर जनताक प्रतिक्रिया समझू।",
    meta_step1: "Meta Analyzer चुनि Instagram अथवा Facebook चुनु।",
    meta_step2: "API वा फाइल अपलोड मोड चुनु।",
    meta_step3: "पोस्टक लिंक दर्ज करू।",
    meta_step4: "'Fetch & Analyze' पर क्लिक कऽ परिणाम देखू।",
    ecom_title: "ई-कॉमर्स विश्लेषक",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO आ Myntra समीक्षा विश्लेषण।",
    ecom_step1: "होम पेज सं 'E-commerce Analyzer' चुनु।",
    ecom_step2: "सामानक लिंक पेस्ट करू।",
    ecom_step3: "सिस्टम अपने-आप प्लेटफॉर्म पहिचानि लेत।",
    ecom_step4: "'Fetch Reviews & Analyze' पर क्लिक कऽ ग्राहकक राय देखू।",
    faq_title: "उपयोगी सुझाव",
    tip1: "रिपोर्ट डाउनलोड: PDF, Excel, CSV वा JSON प्रारूप मे डाउनलोड करू।",
    tip2: "इतिहास: पिछला 20 विश्लेषण History टैब मे सुरक्षित रहैत अछि।",
    tip3: "फाइल अपलोड: अहाँ अपन CSV वा Excel फाइल सेहो अपलोड कऽ सकैत छी।"
  },
  kok: {
    name: "कोंकणी (Konkani)",
    title: "SocialPlus.ai कसो वापरचो",
    subtitle: "YouTube, Meta आनी E-commerce टिप्पण्यांचे विश्लेषण करपा खातीर सोपी मार्गदर्शिका.",
    yt_title: "YouTube विश्लेषक",
    yt_desc: "व्हिडिओ टिप्पण्यांतल्यान प्रेक्षकांच्या प्रतिक्रियांचे विश्लेषण करात.",
    yt_step1: "मुख्य पृष्ठावयल्यान 'YouTube Analyzer' वेंचून काढा.",
    yt_step2: "YouTube व्हिडिओची लिंक पेस्ट करात.",
    yt_step3: "टिप्पण्यांची मर्यादा निवडा (100, 500, 1000+).",
    yt_step4: "'Fetch Comments' चेर क्लिक करून निकाल पळयात.",
    meta_title: "Meta विश्लेषक (Instagram & Facebook)",
    meta_desc: "Instagram आनी Facebook पोस्ट्स वयले विचार जाणून घियात.",
    meta_step1: "Meta Analyzer वेंचून Instagram वा Facebook निवडा.",
    meta_step2: "API वा फाईल अपलोड पर्याय निवडा.",
    meta_step3: "पोस्टाची लिंक घालात.",
    meta_step4: "'Fetch & Analyze' चेर क्लिक करात आनी अहवाल पळयात.",
    ecom_title: "ई-कॉमर्स विश्लेषक",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO आनी Myntra समीक्षण विश्लेषण.",
    ecom_step1: "मुख्यावयल्यान 'E-commerce Analyzer' निवडा.",
    ecom_step2: "उत्पादनाची लिंक पेस्ट करात.",
    ecom_step3: "प्लॅटफॉर्म आपसूक वळखलो वतलो.",
    ecom_step4: "'Fetch Reviews & Analyze' चेर क्लिक करून ग्राहकांचो अभिप्राय पळयात.",
    faq_title: "उपयोगी सुचोवण्यो",
    tip1: "अहवाल डाउनलोड: अहवाल PDF, Excel, CSV वा JSON मदीं डाऊनलोड करात.",
    tip2: "इतिहास: फाटलीं 20 विश्लेषणाम History टॅबांत उपलब्ध आसतात.",
    tip3: "फाईल अपलोड: तुमची CSV वा Excel फाईल थेट अपलोड करूंक शकतात."
  },
  mni: {
    name: "মৈতৈলোন্ (Manipuri)",
    title: "SocialPlus.ai করম্না শিজিন্নগনি",
    subtitle: "YouTube, Meta অমসুং E-commerce কমেন্টশিং নৈননবগী লম্বী।",
    yt_title: "YouTube এনালাইজর",
    yt_desc: "ভিডিও কমেন্টশিংদগী মীয়ামগী ৱাখল্লোন নৈনবীয়ু।",
    yt_step1: "হোম স্ক্রিনদগী 'YouTube Analyzer' খনবীয়ু।",
    yt_step2: "YouTube ভিডিওগী লিঙ্ক পেস্ট তৌবীয়ু।",
    yt_step3: "কমেন্ট মশীং খল্লু (১০০, ৫০০, ১০০০+)।",
    yt_step4: "'Fetch Comments' তা নম্বীয়ু অমসুং AI নৈনবা য়েংবীয়ু।",
    meta_title: "Meta এনালাইজর (Instagram & Facebook)",
    meta_desc: "Instagram অমসুং Facebook পোস্তশিংগী পাউখুম খঙবীয়ু।",
    meta_step1: "Meta Analyzer খনগনি অমসুং Instagram নত্রগা Facebook খনবীয়ু।",
    meta_step2: "API নত্রগা ফাইল অপলোড মোড খনবীয়ু।",
    meta_step3: "পোস্ত লিঙ্ক চনশিল্লু।",
    meta_step4: "'Fetch & Analyze' তা নম্বীয়ু অমসুং রিজাল্ট য়েংবীয়ু।",
    ecom_title: "ই-কমর্স এনালাইজর",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO অমসুং Myntra রিভ্যুগী নৈনবা।",
    ecom_step1: "হোমদগী 'E-commerce Analyzer' খনবীয়ু।",
    ecom_step2: "পোত্থোক্কী লিঙ্ক পেস্ট তৌবীয়ু।",
    ecom_step3: "সিস্তেমনা মশামক প্লেতফোর্ম খঙদোক্কনি।",
    ecom_step4: "'Fetch Reviews & Analyze' তা নম্বীয়ু অমসুং কস্তমরগী ৱাফম য়েংবীয়ু।",
    faq_title: "কান্নবা ৱাফমশিং",
    tip1: "রিপোর্ত দাউনলোদ: PDF, Excel, CSV নত্রগা JSON দা সেভ তৌবীয়ু।",
    tip2: "হিষ্ট্রি: মমাংগী ২০ নৈনবা হিস্ট্রি তেবতা য়েংবা য়াই।",
    tip3: "ফাইল অপলোড: মশাগী CSV নত্রগা Excel ফাইল অপলোড তৌবা য়াই।"
  },
  brx: {
    name: "बड़ो (Bodo)",
    title: "SocialPlus.ai खौ बोरै बाहायनांगौ",
    subtitle: "YouTube, Meta आरो ई-कमर्स बिबुंथिफोरखौ बिजिरनायनि गोरलै लामा।",
    yt_title: "YouTube बिजिरग्रा",
    yt_desc: "भिदिঅ' बिबुंथिफोरनिफ्राय सुबुंफोरनि गोसोआरि साननायखौ बिजिर।",
    yt_step1: "गाहाय बिलाइ निफ्राय 'YouTube Analyzer' खौ सायख'।",
    yt_step2: "YouTube भिदिঅ'नि लिंकखौ फोनांजाब।",
    yt_step3: "बिबुंथिनि अनजिमा सायख' (100, 500, 1000+)।",
    yt_step4: "'Fetch Comments' आव थु आरो AI बिजिरनायखौ नाय।",
    meta_title: "Meta बिजिरग्रा (Instagram & Facebook)",
    meta_desc: "Instagram आरो Facebook नि फोस्टफोरनि बिबुंथिखौ बुजि।",
    meta_step1: "Meta Analyzer खौ सायख'ना Instagram एबा Facebook खौ सायख'।",
    meta_step2: "API एबा फाइल आपलोड लामा सायख'।",
    meta_step3: "फोस्ट लिंकखौ सो।",
    meta_step4: "'Fetch & Analyze' आव थुना फिथाय नाय।",
    ecom_title: "ई-कमर्स बिजिरग्रा",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO आरो Myntra नि बेपारि बिजिरनाय।",
    ecom_step1: "गाहाय बिलाइ निफ्राय 'E-commerce Analyzer' सायख'।",
    ecom_step2: "मुवानि लिंकखौ फोनांजाब।",
    ecom_step3: "सिस्टेमा गावबागावनो प्लेटफर्मखौ सिनायगोन।",
    ecom_step4: "'Fetch Reviews & Analyze' आव थु आरो बायग्राफोरनि साननाय नाय।",
    faq_title: "गोनांथार सोलोफोर",
    tip1: "फोरमान बिलाइ दाउनल'द: PDF, Excel, CSV एबा JSON आव दोन।",
    tip2: "जारिमिन: सिगांनि 20 बिजिरनायफोरखौ History आव नायनो हायो।",
    tip3: "फाइल आपलोड: नोंथांनि CSV एबा Excel फाइलखौ आपलोड खालामनो हायो।"
  },
  sat: {
    name: "ᱥᱟᱱᱛᱟᱲᱤ (Santali)",
    title: "SocialPlus.ai ᱪᱮᱫ ᱞᱮᱠᱟᱛᱮ ᱵᱮᱵᱷᱟᱨᱟ",
    subtitle: "YouTube, Meta ᱟᱨ E-commerce ᱨᱮᱱᱟᱜ ᱠᱚᱢᱮᱱᱴ ᱠᱚ ᱯᱟᱲᱦᱟᱣ ᱟᱨ ᱵᱩᱡᱷᱟᱹᱣ ᱨᱮᱱᱟᱜ ᱜᱟᱭᱤᱰ᱾",
    yt_title: "YouTube ᱮᱱᱟᱞᱟᱭᱡᱟᱨ",
    yt_desc: "ᱵᱷᱤᱰᱤᱭᱳ ᱠᱚᱢᱮᱱᱴ ᱠᱷᱚᱱ ᱧᱮᱧᱮᱞᱤᱭᱟᱹ ᱠᱚᱣᱟᱜ ᱢᱚᱱᱮ ᱵᱩᱡᱷᱟᱹᱣ ᱢᱮ᱾",
    yt_step1: "ᱢᱩᱬᱩᱛ ᱥᱟᱦᱴᱟ ᱠᱷᱚᱱ 'YouTube Analyzer' ᱵᱟᱪᱷᱟᱣ ᱢᱮ᱾",
    yt_step2: "YouTube ᱵᱷᱤᱰᱤᱭᱳ ᱞᱤᱸᱠ ᱯᱮᱥᱴ ᱢᱮ᱾",
    yt_step3: "ᱠᱚᱢᱮᱱᱴ ᱮᱞ (᱑᱐᱐, ᱕᱐᱐, ᱑᱐᱐᱐+) ᱵᱟᱪᱷᱟᱣ ᱢᱮ᱾",
    yt_step4: "'Fetch Comments' ᱨᱮ ᱚᱛᱟ ᱠᱟᱛᱮ AI ᱯᱟᱲᱦᱟᱣ ᱧᱮᱞ ᱢᱮ᱾",
    meta_title: "Meta ᱮᱱᱟᱞᱟᱭᱡᱟᱨ (Instagram & Facebook)",
    meta_desc: "Instagram ᱟᱨ Facebook ᱯᱳᱥᱴ ᱨᱮᱱᱟᱜ ᱠᱚᱢᱮᱱᱴ ᱠᱚ ᱵᱩᱡᱷᱟᱹᱣ ᱢᱮ᱾",
    meta_step1: "Meta Analyzer ᱠᱷᱚᱱ Instagram ᱥᱮ Facebook ᱵᱟᱪᱷᱟᱣ ᱢᱮ᱾",
    meta_step2: "API ᱥᱮ ᱯᱷᱟᱭᱤᱞ ᱟᱯᱞᱳᱰ ᱵᱟᱪᱷᱟᱣ ᱢᱮ᱾",
    meta_step3: "ᱯᱳᱥᱴ ᱞᱤᱸᱠ ᱮᱢ ᱢᱮ᱾",
    meta_step4: "'Fetch & Analyze' ᱨᱮ ᱚᱛᱟ ᱢᱮ᱾",
    ecom_title: "ᱤ-ᱠᱚᱢᱚᱨᱥ ᱮᱱᱟᱞᱟᱭᱡᱟᱨ",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO ᱟᱨ Myntra ᱨᱤᱵᱷᱤᱣ ᱵᱤᱪᱟᱹᱨ᱾",
    ecom_step1: "ᱢᱩᱬᱩᱛ ᱠᱷᱚᱱ 'E-commerce Analyzer' ᱵᱟᱪᱷᱟᱣ ᱢᱮ᱾",
    ecom_step2: "ᱥᱟᱢᱟᱱ ᱨᱮᱱᱟᱜ ᱞᱤᱸᱠ ᱯᱮᱥᱴ ᱢᱮ᱾",
    ecom_step3: "ᱥᱤᱥᱴᱚᱢ ᱟᱡ ᱛᱮᱜᱮ ᱯᱞᱟᱴᱯᱷᱚᱨᱢ ᱩᱨᱩᱢᱟᱭ᱾",
    ecom_step4: "'Fetch Reviews & Analyze' ᱨᱮ ᱚᱛᱟ ᱠᱟᱛᱮ ᱠᱤᱨᱤᱧᱤᱭᱟᱹ ᱠᱚᱣᱟᱜ ᱢᱚᱱᱮ ᱧᱮᱞ ᱢᱮ᱾",
    faq_title: "ᱞᱟᱹᱠᱛᱤᱭᱟᱱ ᱠᱟᱛᱷᱟ",
    tip1: "ᱨᱤᱯᱳᱨᱴ ᱰᱟᱩᱱᱞᱳᱰ: PDF, Excel, CSV ᱥᱮ JSON ᱛᱮ ᱰᱟᱩᱱᱞᱳᱰ ᱢᱮ᱾",
    tip2: "ᱱᱟᱜᱟᱢ: ᱢᱟᱲᱟᱝ ᱨᱮᱱᱟᱜ ᱒᱐ ᱜᱚᱴᱟᱝ ᱵᱤᱪᱟᱹᱨ History ᱨᱮ ᱛᱟᱦᱮᱸᱱᱟ᱾",
    tip3: "ᱯᱷᱟᱭᱤᱞ ᱟᱯᱞᱳᱰ: ᱟᱢᱟᱜ CSV ᱥᱮ Excel ᱯᱷᱟᱭᱤᱞ ᱟᱯᱞᱳᱰ ᱫᱟᱲᱮᱭᱟᱜᱼᱟᱢ᱾"
  },
  doi: {
    name: "डोगरी (Dogri)",
    title: "SocialPlus.ai गी किश चालाना",
    subtitle: "YouTube, Meta ते E-commerce टिप्पणियें दा विश्लेषण करने लेई आसान मार्गदर्शिका।",
    yt_title: "YouTube विश्लेषक",
    yt_desc: "वीडियो टिप्पणियें थ्हवां दर्शके दी राय ते भावनाएं दा विश्लेषण करो।",
    yt_step1: "होम स्क्रीन थ्हवां 'YouTube Analyzer' चुनो।",
    yt_step2: "YouTube वीडियो दा लिंक पेस्ट करो।",
    yt_step3: "टिप्पणियें दी गिनती (100, 500, 1000+) चुनो।",
    yt_step4: "'Fetch Comments' पर क्लिक करी कन्ने AI नतीजे दिक्खो।",
    meta_title: "Meta विश्लेषक (Instagram ते Facebook)",
    meta_desc: "Instagram ते Facebook पोस्टें पर जनता दा रुझान समझो।",
    meta_step1: "Meta Analyzer चुनी कन्ने Instagram या Facebook चुनो।",
    meta_step2: "API या फाइल अपलोड विकल्प चुनो।",
    meta_step3: "पोस्ट लिंक दर्ज करो।",
    meta_step4: "'Fetch & Analyze' पर क्लिक करी कन्ने रिपोर्ट हासल करो।",
    ecom_title: "ई-कॉमर्स विश्लेषक",
    ecom_desc: "Amazon, Flipkart, Meesho, Jio/AJIO ते Myntra समीक्षा विश्लेषण।",
    ecom_step1: "होम पेजा थ्हवां 'E-commerce Analyzer' चुनो।",
    ecom_step2: "सामान दा लिंक पेस्ट करो।",
    ecom_step3: "सिस्टम आपू प्लेटफ़ॉर्म पन्छानी लैग।",
    ecom_step4: "'Fetch Reviews & Analyze' पर क्लिक करी कन्ने ग्राहके दी राय दिक्खो।",
    faq_title: "जरूरी सुझाव",
    tip1: "रिपोर्ट डाउनलोड: PDF, Excel, CSV या JSON च डाउनलोड करो।",
    tip2: "इतिहास: पिछला 20 विश्लेषण History टैब च दिक्खे जाई सकदे न।",
    tip3: "फाइल अपलोड: तुस अपनी CSV या Excel फाइल वी अपलोड करी सकदे ओ।"
  }
};

function renderHowToUseGuide(langCode = "en") {
  const data = HOW_TO_USE_LANGUAGES[langCode] || HOW_TO_USE_LANGUAGES.en;
  const container = document.getElementById("howtouse-content");
  if (!container) return;

  container.innerHTML = `
    <div class="glass-guide-header">
      <h2 class="glass-guide-title">${data.title}</h2>
      <p class="glass-guide-subtitle">${data.subtitle}</p>
    </div>

    <div class="glass-guide-grid">
      <!-- YouTube Guide Card -->
      <div class="glass-guide-card">
        <div class="guide-card-icon yt">
          <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
        </div>
        <h3 class="guide-card-title">${data.yt_title}</h3>
        <p class="guide-card-desc">${data.yt_desc}</p>
        <ol class="guide-steps-list">
          <li><strong>Step 1:</strong> ${data.yt_step1}</li>
          <li><strong>Step 2:</strong> ${data.yt_step2}</li>
          <li><strong>Step 3:</strong> ${data.yt_step3}</li>
          <li><strong>Step 4:</strong> ${data.yt_step4}</li>
        </ol>
      </div>

      <!-- Meta Guide Card -->
      <div class="glass-guide-card">
        <div class="guide-card-icon meta">
          <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
        </div>
        <h3 class="guide-card-title">${data.meta_title}</h3>
        <p class="guide-card-desc">${data.meta_desc}</p>
        <ol class="guide-steps-list">
          <li><strong>Step 1:</strong> ${data.meta_step1}</li>
          <li><strong>Step 2:</strong> ${data.meta_step2}</li>
          <li><strong>Step 3:</strong> ${data.meta_step3}</li>
          <li><strong>Step 4:</strong> ${data.meta_step4}</li>
        </ol>
      </div>

      <!-- E-commerce Guide Card -->
      <div class="glass-guide-card">
        <div class="guide-card-icon ecom">
          <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path><line x1="3" y1="6" x2="21" y2="6"></line><path d="M16 10a4 4 0 0 1-8 0"></path></svg>
        </div>
        <h3 class="guide-card-title">${data.ecom_title}</h3>
        <p class="guide-card-desc">${data.ecom_desc}</p>
        <ol class="guide-steps-list">
          <li><strong>Step 1:</strong> ${data.ecom_step1}</li>
          <li><strong>Step 2:</strong> ${data.ecom_step2}</li>
          <li><strong>Step 3:</strong> ${data.ecom_step3}</li>
          <li><strong>Step 4:</strong> ${data.ecom_step4}</li>
        </ol>
      </div>
    </div>

    <!-- Pro Tips Box -->
    <div class="glass-guide-tips">
      <h4 class="tips-heading">
        <span class="gold-star">★</span> ${data.faq_title}
      </h4>
      <div class="tips-grid">
        <div class="tip-item">
          <strong>1.</strong> ${data.tip1}
        </div>
        <div class="tip-item">
          <strong>2.</strong> ${data.tip2}
        </div>
        <div class="tip-item">
          <strong>3.</strong> ${data.tip3}
        </div>
      </div>
    </div>
  `;
}

window.renderHowToUseGuide = renderHowToUseGuide;
window.renderHowToUseLanguage = renderHowToUseGuide;
window.initHowToUse = function() {
  const select = document.getElementById("howtouse-lang-select");
  const lang = select ? select.value : "en";
  renderHowToUseGuide(lang || "en");
};

document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("howtouse-lang-select");
  if (select) {
    select.addEventListener("change", (e) => {
      renderHowToUseGuide(e.target.value);
    });
  }
  renderHowToUseGuide("en");
});
