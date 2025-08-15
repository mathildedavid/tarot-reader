from flask import Flask, render_template, request, jsonify
import random
import os

app = Flask(__name__)

# Try to import anthropic, fallback if not available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    client = None  # Initialize as None first
    
    if ANTHROPIC_API_KEY:
        try:
            # Try to create the client, but catch any errors
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            print("✅ Anthropic API configured")
        except Exception as e:
            # If client creation fails, don't crash - just use fallback
            print(f"⚠️ Anthropic client initialization failed: {e}")
            ANTHROPIC_AVAILABLE = False
            client = None
    else:
        print("⚠️ ANTHROPIC_API_KEY not set - using fallback readings")
        ANTHROPIC_AVAILABLE = False
        client = None
except ImportError:
    print("⚠️ Anthropic library not installed - using fallback readings")
    ANTHROPIC_AVAILABLE = False
    client = None

CARDS = [
    {"name": "The Fool", "symbol": "🌟", "meaning": "New beginnings, spontaneity, innocence", 
     "keywords": ["new start", "adventure", "leap of faith", "innocence", "potential"]},
    {"name": "The Magician", "symbol": "🎭", "meaning": "Manifestation, resourcefulness, power", 
     "keywords": ["manifestation", "skill", "concentration", "action", "resourcefulness"]},
    {"name": "The High Priestess", "symbol": "🌙", "meaning": "Intuition, sacred knowledge, divine feminine", 
     "keywords": ["intuition", "mystery", "subconscious", "wisdom", "spiritual insight"]},
    {"name": "The Empress", "symbol": "👸", "meaning": "Femininity, beauty, nature, nurturing", 
     "keywords": ["fertility", "femininity", "beauty", "nature", "abundance"]},
    {"name": "The Emperor", "symbol": "👑", "meaning": "Authority, establishment, structure", 
     "keywords": ["authority", "father figure", "structure", "control", "power"]},
    {"name": "The Hierophant", "symbol": "⛪", "meaning": "Spiritual wisdom, religious beliefs, tradition", 
     "keywords": ["tradition", "conformity", "morality", "ethics", "knowledge"]},
    {"name": "The Lovers", "symbol": "💕", "meaning": "Love, harmony, relationships, values", 
     "keywords": ["love", "harmony", "relationships", "values", "choices"]},
    {"name": "The Chariot", "symbol": "🏆", "meaning": "Control, willpower, success, determination", 
     "keywords": ["control", "willpower", "success", "determination", "hard control"]},
    {"name": "Strength", "symbol": "🦁", "meaning": "Strength, courage, persuasion, influence", 
     "keywords": ["strength", "courage", "persuasion", "influence", "compassion"]},
    {"name": "The Hermit", "symbol": "🕯️", "meaning": "Soul searching, introspection, inner guidance", 
     "keywords": ["introspection", "searching", "guidance", "solitude", "inner wisdom"]},
    {"name": "Wheel of Fortune", "symbol": "🎡", "meaning": "Good luck, karma, life cycles, destiny", 
     "keywords": ["luck", "karma", "cycles", "destiny", "fortune"]},
    {"name": "Justice", "symbol": "⚖️", "meaning": "Justice, fairness, truth, cause and effect", 
     "keywords": ["justice", "fairness", "truth", "law", "karma"]},
    {"name": "The Hanged Man", "symbol": "🙃", "meaning": "Suspension, restriction, letting go", 
     "keywords": ["suspension", "restriction", "letting go", "sacrifice", "martyrdom"]},
    {"name": "Death", "symbol": "💀", "meaning": "Endings, transformation, transition", 
     "keywords": ["endings", "transformation", "transition", "change", "rebirth"]},
    {"name": "Temperance", "symbol": "🍷", "meaning": "Balance, moderation, patience, purpose", 
     "keywords": ["balance", "moderation", "patience", "purpose", "meaning"]},
    {"name": "The Devil", "symbol": "😈", "meaning": "Bondage, addiction, sexuality", 
     "keywords": ["bondage", "addiction", "sexuality", "materialism", "playfulness"]},
    {"name": "The Tower", "symbol": "🗼", "meaning": "Sudden change, upheaval, chaos, revelation", 
     "keywords": ["sudden change", "upheaval", "chaos", "revelation", "awakening"]},
    {"name": "The Star", "symbol": "⭐", "meaning": "Hope, faith, purpose, renewal, spirituality", 
     "keywords": ["hope", "faith", "purpose", "renewal", "spirituality"]},
    {"name": "The Moon", "symbol": "🌕", "meaning": "Illusion, fear, anxiety, subconscious, intuition", 
     "keywords": ["illusion", "fear", "anxiety", "subconscious", "intuition"]},
    {"name": "The Sun", "symbol": "☀️", "meaning": "Positivity, fun, warmth, success, vitality", 
     "keywords": ["positivity", "fun", "warmth", "success", "vitality"]},
    {"name": "Judgement", "symbol": "📯", "meaning": "Judgement, rebirth, inner calling, absolution", 
     "keywords": ["judgement", "rebirth", "inner calling", "absolution", "second chances"]},
    {"name": "The World", "symbol": "🌍", "meaning": "Completion, accomplishment, travel", 
     "keywords": ["completion", "accomplishment", "travel", "fulfillment", "success"]},
]

def determine_context(question):
    """Determine the context of the question"""
    question_lower = question.lower()
    
    love_keywords = ['love', 'relationship', 'romance', 'partner', 'dating', 'marriage', 'heart', 'feelings']
    career_keywords = ['career', 'job', 'work', 'business', 'money', 'success', 'professional', 'promotion']
    
    if any(keyword in question_lower for keyword in love_keywords):
        return 'love'
    elif any(keyword in question_lower for keyword in career_keywords):
        return 'career'
    else:
        return 'general'

def generate_fallback_reading(question, card):
    """Generate a reading without AI as fallback"""
    context = determine_context(question)
    
    reading_templates = {
        'love': f"""CARD MESSAGE:
The {card['name']} speaks to matters of the heart with profound wisdom. In your question about love and relationships, this card suggests that {card['meaning'].lower()} will play a crucial role in your romantic journey.

HOW THIS RELATES TO YOU:
The energy of {card['keywords'][0]} and {card['keywords'][1]} is particularly relevant to your current relationship situation. Consider how embracing {card['keywords'][2]} might transform your current relationship dynamics.

GUIDANCE AND INSIGHTS:
- Focus on cultivating {card['keywords'][0]} in your romantic connections
- Allow {card['keywords'][1]} to guide your decisions in matters of the heart  
- Remember that {card['keywords'][3]} will help you move forward with greater clarity

MOVING FORWARD:
Trust in the process and remain open to the lessons this card offers for your romantic growth.

KEY TAKEAWAY:
Love flourishes when you embrace the energy of {card['keywords'][4]} and trust in your heart's wisdom.""",
        
        'career': f"""CARD MESSAGE:
In matters of career and professional growth, the {card['name']} offers powerful guidance. This card embodies {card['meaning'].lower()}, suggesting that your professional path requires focus on these qualities.

HOW THIS RELATES TO YOU:
Your career question aligns perfectly with the energy of {card['keywords'][0]} and {card['keywords'][1]}. This card's appearance indicates significant opportunities for professional development.

GUIDANCE AND INSIGHTS:
- Embrace {card['keywords'][0]} as a key to unlocking career opportunities
- Use {card['keywords'][1]} to navigate workplace challenges with confidence
- Focus on developing {card['keywords'][2]} to advance your professional goals

MOVING FORWARD:
Trust in the process and remain open to new opportunities that align with your authentic professional self.

KEY TAKEAWAY:
Your career success depends on incorporating {card['keywords'][4]} into your professional approach.""",
        
        'general': f"""CARD MESSAGE:
The {card['name']} emerges to guide you through your current situation. This powerful card represents {card['meaning'].lower()}, offering insights that directly relate to your inquiry.

HOW THIS RELATES TO YOU:
The cosmic forces have aligned to bring you energies of {card['keywords'][0]} and {card['keywords'][1]}. These themes are particularly relevant to your current life circumstances.

GUIDANCE AND INSIGHTS:
- Embrace the quality of {card['keywords'][0]} to navigate your current challenges
- Allow {card['keywords'][1]} to inform your decisions and actions
- Trust that {card['keywords'][2]} will guide you toward the right path

MOVING FORWARD:
Focus on integrating these insights into your daily life and trust in your inner wisdom.

KEY TAKEAWAY:
You have the power to shape your destiny by embracing {card['keywords'][4]} and trusting in your authentic self."""
    }
    
    return reading_templates.get(context, reading_templates['general'])

def generate_ai_reading(question, card):
    """Generate a personalized tarot reading using Anthropic's Claude"""
    
    # Check if API is available and configured
    if not ANTHROPIC_AVAILABLE or not ANTHROPIC_API_KEY:
        print("🔄 Using fallback reading (no AI)")
        return generate_fallback_reading(question, card)
    
    prompt = f"""You are an experienced, wise tarot reader. A person has drawn the tarot card "{card['name']}" and shared: "{question}"

The card represents: {card['meaning']}
Key themes: {', '.join(card['keywords'])}

Please provide a structured tarot reading using this exact format (use EXACTLY these section headers):

CARD MESSAGE:
[2-3 sentences explaining what this card means for their situation]

HOW THIS RELATES TO YOU:
[2-3 sentences connecting the card specifically to their context]

GUIDANCE AND INSIGHTS:
- [First key insight or advice]
- [Second key insight or advice] 
- [Third key insight or advice]

MOVING FORWARD:
[1-2 sentences with practical next steps]

KEY TAKEAWAY:
[One powerful sentence summarizing the main message]

Use a warm, wise, and empowering tone. Make each section meaningful and specific to their situation."""

    try:
        print(f"🤖 Generating AI reading for: {card['name']}")
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        print("✅ AI reading generated successfully")
        return message.content[0].text
        
    except Exception as e:
        print(f"❌ Error generating AI reading: {e}")
        print(f"Error type: {type(e).__name__}")
        print("🔄 Falling back to template reading")
        return generate_fallback_reading(question, card)

@app.route("/")
def home():
    api_status = "🤖 AI-powered readings" if (ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY) else "📖 Template readings"
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Tarot Card Reader</title>
    <style>
        body {{ 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 700px; 
            margin: 40px auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            line-height: 1.6;
        }}
        .container {{ 
            background: white; 
            padding: 40px; 
            border-radius: 20px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .status {{
            background: #f1f5f9;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            color: #64748B;
            margin-bottom: 20px;
            display: inline-block;
        }}
        h1 {{ 
            color: #6B73FF; 
            margin-bottom: 10px;
            font-size: 2.5em;
            font-weight: 700;
        }}
        .subtitle {{
            color: #64748B;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        .question-section {{
            text-align: left;
            margin: 30px 0;
            padding: 25px;
            background: #f8fafc;
            border-radius: 15px;
            border: 1px solid #e2e8f0;
        }}
        label {{
            display: block;
            font-weight: 600;
            color: #334155;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .context-note {{
            font-size: 0.9em;
            color: #64748B;
            margin-bottom: 10px;
            line-height: 1.4;
        }}
        textarea {{
            width: 100%;
            height: 120px;
            padding: 15px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            transition: border-color 0.2s;
            box-sizing: border-box;
        }}
        textarea:focus {{
            outline: none;
            border-color: #6B73FF;
            box-shadow: 0 0 0 3px rgba(107, 115, 255, 0.1);
        }}
        .char-count {{
            text-align: right;
            margin-top: 5px;
            font-size: 0.9em;
            color: #64748B;
        }}
        button {{ 
            background: linear-gradient(135deg, #6B73FF 0%, #9333EA 100%);
            color: white; 
            padding: 15px 30px; 
            border: none; 
            border-radius: 50px; 
            cursor: pointer; 
            font-size: 18px;
            font-weight: 600;
            margin: 20px 0;
            transition: all 0.3s ease;
            min-width: 200px;
        }}
        button:hover {{ 
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(107, 115, 255, 0.3);
        }}
        button:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }}
        .card-result {{ 
            border: 2px solid #6B73FF; 
            padding: 30px; 
            margin: 30px 0; 
            border-radius: 15px; 
            background: linear-gradient(135deg, #f8faff 0%, #f1f5ff 100%);
            display: none;
        }}
        .card-result.show {{
            display: block;
            animation: fadeIn 0.5s ease-in;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .symbol {{ 
            font-size: 5em; 
            margin: 20px 0; 
        }}
        .card-name {{
            font-size: 1.8em;
            font-weight: 700;
            color: #6B73FF;
            margin-bottom: 20px;
        }}
        .card-meaning {{
            font-size: 1.1em;
            color: #64748B;
            margin-bottom: 25px;
            font-style: italic;
        }}
        .reading {{
            text-align: left;
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-top: 25px;
            border-left: 4px solid #6B73FF;
            font-size: 1.05em;
            line-height: 1.7;
        }}
        .reading-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: #6B73FF;
            margin-bottom: 15px;
        }}
        .reading h4 {{
            color: #6B73FF;
            font-size: 1.1em;
            margin: 20px 0 10px 0;
            font-weight: 600;
            border-bottom: 1px solid #f1f5ff;
            padding-bottom: 5px;
        }}
        .reading ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .reading li {{
            margin: 8px 0;
            line-height: 1.6;
            list-style-type: disc;
        }}
        .reading p {{
            margin: 10px 0;
            line-height: 1.7;
        }}
        .loading {{
            color: #6B73FF;
            font-style: italic;
        }}
        .spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #e2e8f0;
            border-radius: 50%;
            border-top-color: #6B73FF;
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        .reset-btn {{
            background: transparent;
            color: #6B73FF;
            border: 2px solid #6B73FF;
            padding: 10px 20px;
            font-size: 16px;
            min-width: auto;
        }}
        .reset-btn:hover {{
            background: #6B73FF;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="status">{api_status}</div>
        <h1>🔮 Tarot Card Reader</h1>
        <p class="subtitle">Ask a question and receive personalized guidance from the cards</p>
        
        <div class="question-section">
            <label for="question">What guidance are you seeking today?</label>
            <p class="context-note">
                Share both your question and the context around your situation. The more details you provide, the more personalized and relevant your reading will be.
            </p>
            <textarea 
                id="question" 
                placeholder="Example: 'What should I be reminded of today? (You can add context too!)'"
                maxlength="800"
                oninput="updateCharCount()"
            ></textarea>
            <div class="char-count">
                <span id="charCount">0</span>/800
            </div>
        </div>
        
        <button id="drawBtn" onclick="drawCard()">
            Draw Your Card
        </button>
        
        <div id="cardResult" class="card-result">
            <div class="card-name" id="cardName"></div>
            <div class="symbol" id="cardSymbol"></div>
            <div class="card-meaning" id="cardMeaning"></div>
            
            <div class="reading">
                <div class="reading-title">Your Personal Reading</div>
                <div id="readingText"></div>
            </div>
            
            <button class="reset-btn" onclick="resetCard()">
                Ask Another Question
            </button>
        </div>
    </div>

    <script>
        function updateCharCount() {{
            const textarea = document.getElementById('question');
            const charCount = document.getElementById('charCount');
            charCount.textContent = textarea.value.length;
        }}

        async function drawCard() {{
            const question = document.getElementById('question').value.trim();
            const drawBtn = document.getElementById('drawBtn');
            const cardResult = document.getElementById('cardResult');
            
            if (!question) {{
                alert('Please enter your question first!');
                return;
            }}
            
            if (question.length < 20) {{
                alert('Please provide more context along with your question for a more meaningful reading.');
                return;
            }}
            
            // Show loading state
            drawBtn.disabled = true;
            drawBtn.innerHTML = '<span class="spinner"></span>Drawing your card...';
            cardResult.classList.remove('show');
            
            try {{
                const response = await fetch('/draw-card', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ question: question }})
                }});
                
                const data = await response.json();
                
                if (data.error) {{
                    alert('Error: ' + data.error);
                    return;
                }}
                
                // Update card display
                document.getElementById('cardName').textContent = data.card.name;
                document.getElementById('cardSymbol').textContent = data.card.symbol;
                document.getElementById('cardMeaning').textContent = data.card.meaning;
                
                // Simple formatting that actually works
                let formattedReading = data.reading;

                // Format section headers
                formattedReading = formattedReading.replace(/CARD MESSAGE:/g, '<h4>💫 Card Message:</h4>');
                formattedReading = formattedReading.replace(/HOW THIS RELATES TO YOU:/g, '<h4>🔍 How This Relates to You:</h4>');
                formattedReading = formattedReading.replace(/GUIDANCE AND INSIGHTS:/g, '<h4>✨ Guidance & Insights:</h4>');
                formattedReading = formattedReading.replace(/MOVING FORWARD:/g, '<h4>🚀 Moving Forward:</h4>');
                formattedReading = formattedReading.replace(/KEY TAKEAWAY:/g, '<h4>🌟 Key Takeaway:</h4>');

                // Convert bullet points that start with -
                formattedReading = formattedReading.replace(/^- (.+)$/gm, '<li>$1</li>');

                // Simple list wrapping
                formattedReading = formattedReading.replace(/(<li>.*?<\\/li>)/gs, '<ul>$1</ul>');

                // Convert line breaks to paragraphs
                formattedReading = formattedReading.replace(/\\n\\n/g, '</p><p>');
                formattedReading = formattedReading.replace(/\\n/g, '<br>');

                // Wrap in paragraphs if needed
                if (!formattedReading.includes('<p>')) {{
                    formattedReading = '<p>' + formattedReading + '</p>';
                }}

                document.getElementById('readingText').innerHTML = formattedReading;
                
                // Show result
                cardResult.classList.add('show');
                
                // Scroll to result
                cardResult.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                
            }} catch (error) {{
                alert('Something went wrong. Please try again.');
                console.error('Error:', error);
            }} finally {{
                // Reset button
                drawBtn.disabled = false;
                drawBtn.innerHTML = 'Draw Your Card';
            }}
        }}
        
        function resetCard() {{
            document.getElementById('question').value = '';
            document.getElementById('cardResult').classList.remove('show');
            updateCharCount();
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
        
        // Allow Enter + Cmd/Ctrl to submit
        document.getElementById('question').addEventListener('keydown', function(e) {{
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {{
                e.preventDefault();
                drawCard();
            }}
        }});
    </script>
</body>
</html>
"""

@app.route('/draw-card', methods=['POST'])
def draw_card():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Please enter your question first!'}), 400
        
        # Select random card
        card = random.choice(CARDS)
        print(f"🎴 Card drawn: {card['name']}")
        
        # Generate reading
        reading = generate_ai_reading(question, card)
        
        return jsonify({
            'card': card,
            'reading': reading
        })
        
    except Exception as e:
        print(f"❌ Error in draw_card route: {e}")
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500

if __name__ == '__main__':
    print("🔮 Enhanced Tarot Reader starting...")
    
    # Get port from environment for deployment, default to 5000 for local
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0' if os.environ.get('PORT') else '127.0.0.1'
    debug = not os.environ.get('PORT')  # Only debug locally
    
    if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
        print("🤖 AI readings enabled")
    else:
        print("📖 Using template readings")
    
    print(f"📱 Go to: http://{host}:{port}")
    app.run(debug=debug, host=host, port=port)