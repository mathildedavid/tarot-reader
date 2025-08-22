import openai
import requests
import os
from typing import List, Dict
import time
import base64
import glob
import re

# Configure your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Alternative API configurations
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

# Major Arcana cards with their traditional names
MAJOR_ARCANA: List[Dict[str, str]] = [
    {"number": "0", "name": "The Fool", "filename": "00_the_fool"},
    {"number": "I", "name": "The Magician", "filename": "01_the_magician"},
    {"number": "II", "name": "The High Priestess", "filename": "02_the_high_priestess"},
    {"number": "III", "name": "The Empress", "filename": "03_the_empress"},
    {"number": "IV", "name": "The Emperor", "filename": "04_the_emperor"},
    {"number": "V", "name": "The Hierophant", "filename": "05_the_hierophant"},
    {"number": "VI", "name": "The Lovers", "filename": "06_the_lovers"},
    {"number": "VII", "name": "The Chariot", "filename": "07_the_chariot"},
    {"number": "VIII", "name": "Strength", "filename": "08_strength"},
    {"number": "IX", "name": "The Hermit", "filename": "09_the_hermit"},
    {"number": "X", "name": "Wheel of Fortune", "filename": "10_wheel_of_fortune"},
    {"number": "XI", "name": "Justice", "filename": "11_justice"},
    {"number": "XII", "name": "The Hanged Man", "filename": "12_the_hanged_man"},
    {"number": "XIII", "name": "Death", "filename": "13_death"},
    {"number": "XIV", "name": "Temperance", "filename": "14_temperance"},
    {"number": "XV", "name": "The Devil", "filename": "15_the_devil"},
    {"number": "XVI", "name": "The Tower", "filename": "16_the_tower"},
    {"number": "XVII", "name": "The Star", "filename": "17_the_star"},
    {"number": "XVIII", "name": "The Moon", "filename": "18_the_moon"},
    {"number": "XIX", "name": "The Sun", "filename": "19_the_sun"},
    {"number": "XX", "name": "Judgement", "filename": "20_judgement"},
    {"number": "XXI", "name": "The World", "filename": "21_the_world"}
]

def create_prompt(card_name: str) -> str:
    """Create the detailed prompt for each tarot card."""
    base_prompt = """Create a complete tarot card in a 2:3 aspect ratio that fits entirely within the frame borders with transparent margins around all edges. The card should not be truncated. It should be in traditional rectangular format (taller than wide), showing the FULL card from top border to bottom border with generous transparent space on all sides. The image should be a bird's eye view of the entire tarot card laying flat with a transparent background surrounding the card, displaying intricate gold and silver foil embellishments, rich jewel-tone colors, and a magical, occult atmosphere. Include thick decorative borders on all four sides with swirling floral and celestial patterns reminiscent of illuminated manuscripts and Art Nouveau. The central scene should depict **{}**, faithful to the Rider-Waite-Smith symbolism but enhanced with modern high-end fantasy art detailing. The textures should shimmer as if printed with metallic foil on high-quality cardstock, with dramatic lighting and mystical grandeur. Ensure the ENTIRE card is visible with transparent margins around all edges, like viewing a complete tarot card floating on a transparent background."""
    
    # Add to your prompt:
    #"Design a complete tarot card in a 2:3 aspect ratio that fits entirely within the frame borders. Include generous transparent margins around all artwork. The composition should be sized to ensure nothing is cut off at the edges - all imagery, decorative elements, and title text must be fully visible with transparent space around them. Think of it as artwork designed to fit within a border with proper transparent margins, not artwork that extends to the edges."
    # Special handling for cards that might trigger safety filters
    safe_modifications = {
        "Judgement": "Create a complete tarot card in traditional rectangular format (taller than wide), showing the FULL card from top border to bottom border with generous transparent margins on all sides. The image should be a bird's eye view of the entire tarot card laying flat with a transparent background surrounding the card, displaying intricate gold and silver foil embellishments, rich jewel-tone colors, and a magical, occult atmosphere. Include thick decorative borders on all four sides with swirling floral and celestial patterns reminiscent of illuminated manuscripts and Art Nouveau. The central scene should depict **Judgement** with an angel blowing a trumpet in cloudy skies above, and fully clothed figures rising with arms raised in reverence below, faithful to tarot symbolism but tasteful and appropriate. The textures should shimmer as if printed with metallic foil on high-quality cardstock, with dramatic lighting and mystical grandeur. Ensure the ENTIRE card is visible with transparent margins around all edges, like viewing a complete tarot card floating on a transparent background.",
        "The Devil": "Create a complete tarot card in traditional rectangular format (taller than wide), showing the FULL card from top border to bottom border with generous transparent margins on all sides. The image should be a bird's eye view of the entire tarot card laying flat with a transparent background surrounding the card, displaying intricate gold and silver foil embellishments, rich jewel-tone colors, and a magical, occult atmosphere. Include thick decorative borders on all four sides with swirling floral and celestial patterns reminiscent of illuminated manuscripts and Art Nouveau. The central scene should depict **The Devil** as a horned figure on a throne with chained figures below, all fully clothed and tastefully depicted, faithful to tarot symbolism. The textures should shimmer as if printed with metallic foil on high-quality cardstock, with dramatic lighting and mystical grandeur. Ensure the ENTIRE card is visible with transparent margins around all edges, like viewing a complete tarot card floating on a transparent background.",
        "The Star": "Create a complete tarot card in traditional rectangular format (taller than wide), showing the FULL card from top border to bottom border with generous transparent margins on all sides. The image should be a bird's eye view of the entire tarot card laying flat with a transparent background surrounding the card, displaying intricate gold and silver foil embellishments, rich jewel-tone colors, and a magical, occult atmosphere. Include thick decorative borders on all four sides with swirling floral and celestial patterns reminiscent of illuminated manuscripts and Art Nouveau. The central scene should depict **The Star** with a modestly clothed figure pouring water under starry skies, faithful to tarot symbolism but appropriate and tasteful. The textures should shimmer as if printed with metallic foil on high-quality cardstock, with dramatic lighting and mystical grandeur. Ensure the ENTIRE card is visible with transparent margins around all edges, like viewing a complete tarot card floating on a transparent background.",
        "The Lovers": "Create a complete tarot card in traditional rectangular format (taller than wide), showing the FULL card from top border to bottom border with generous transparent margins on all sides. The image should be a bird's eye view of the entire tarot card laying flat with a transparent background surrounding the card, displaying intricate gold and silver foil embellishments, rich jewel-tone colors, and a magical, occult atmosphere. Include thick decorative borders on all four sides with swirling floral and celestial patterns reminiscent of illuminated manuscripts and Art Nouveau. The central scene should depict **The Lovers** as fully clothed figures standing together under an angelic presence, faithful to tarot symbolism but appropriate and tasteful. The textures should shimmer as if printed with metallic foil on high-quality cardstock, with dramatic lighting and mystical grandeur. Ensure the ENTIRE card is visible with transparent margins around all edges, like viewing a complete tarot card floating on a transparent background.",
        "The Hanged Man": "Create a complete tarot card in traditional rectangular format (taller than wide), showing the FULL card from top border to bottom border with generous transparent margins on all sides. The image should be a bird's eye view of the entire tarot card laying flat with a transparent background surrounding the card, displaying intricate gold and silver foil embellishments, rich jewel-tone colors, and a magical, occult atmosphere. Include thick decorative borders on all four sides with swirling floral and celestial patterns reminiscent of illuminated manuscripts and Art Nouveau. The central scene should depict **The Hanged Man** as a fully clothed figure suspended upside down from a tree, with a serene expression and golden halo, faithful to tarot symbolism but appropriate and tasteful. The textures should shimmer as if printed with metallic foil on high-quality cardstock, with dramatic lighting and mystical grandeur. Ensure the ENTIRE card is visible with transparent margins around all edges, like viewing a complete tarot card floating on a transparent background.",
        "The Sun": "Create a complete tarot card in traditional rectangular format (taller than wide), showing the FULL card from top border to bottom border with generous transparent margins on all sides. The image should be a bird's eye view of the entire tarot card laying flat with a transparent background surrounding the card, displaying intricate gold and silver foil embellishments, rich jewel-tone colors, and a magical, occult atmosphere. Include thick decorative borders on all four sides with swirling floral and celestial patterns reminiscent of illuminated manuscripts and Art Nouveau. The central scene should depict **The Sun** with a fully clothed child riding a white horse under a radiant sun, faithful to tarot symbolism but appropriate and tasteful. The textures should shimmer as if printed with metallic foil on high-quality cardstock, with dramatic lighting and mystical grandeur. Ensure the ENTIRE card is visible with transparent margins around all edges, like viewing a complete tarot card floating on a transparent background."
    }
    
    if card_name in safe_modifications:
        return safe_modifications[card_name]
    else:
        return base_prompt.format(card_name)

def get_next_version_number(filename: str, output_dir: str = "tarot_cards") -> int:
    """Get the next version number for a card."""
    pattern = f"{filename}_v*.png"
    existing_files = glob.glob(os.path.join(output_dir, pattern))
    
    if not existing_files:
        return 1
    
    version_numbers = []
    for file_path in existing_files:
        basename = os.path.basename(file_path)
        match = re.search(r'_v(\d+)\.png$', basename)
        if match:
            version_numbers.append(int(match.group(1)))
    
    return max(version_numbers) + 1 if version_numbers else 1

def update_latest_symlink(filename: str, version_num: int, output_dir: str = "tarot_cards"):
    """Create or update the _latest symlink/copy."""
    versioned_file = os.path.join(output_dir, f"{filename}_v{version_num}.png")
    latest_file = os.path.join(output_dir, f"{filename}_latest.png")
    
    # Remove existing latest file if it exists
    if os.path.exists(latest_file):
        os.remove(latest_file)
    
    # Create a copy (since symlinks can be problematic on some systems)
    if os.path.exists(versioned_file):
        import shutil
        shutil.copy2(versioned_file, latest_file)
        print(f"📌 Updated latest: {filename}_latest.png")

def generate_image_openai(prompt: str, filename: str, output_dir: str = "tarot_cards") -> bool:
    """Generate an image using OpenAI's GPT-Image-1 API with versioning."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Get next version number
        version_num = get_next_version_number(filename, output_dir)
        versioned_filename = f"{filename}_v{version_num}"
        
        response = openai.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1536",
            quality="high",
            n=1
        )
        
        # GPT-Image-1 returns base64 data
        if hasattr(response, 'data') and response.data:
            image_data_obj = response.data[0]
            
            if hasattr(image_data_obj, 'b64_json') and image_data_obj.b64_json:
                image_data = base64.b64decode(image_data_obj.b64_json)
                
                # Save versioned file
                filepath = os.path.join(output_dir, f"{versioned_filename}.png")
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                # Update latest file
                update_latest_symlink(filename, version_num, output_dir)
                
                print(f"✅ Successfully generated: {versioned_filename}.png")
                return True
        
        print(f"❌ No valid image data found in response for {filename}")
        return False
            
    except Exception as e:
        print(f"❌ Error generating {filename}: {str(e)}")
        return False

def generate_image_stability(prompt: str, filename: str, output_dir: str = "tarot_cards") -> bool:
    """Generate an image using Stability AI's API."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {STABILITY_API_KEY}",
        }
        
        body = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            image_data = base64.b64decode(data["artifacts"][0]["base64"])
            
            filepath = os.path.join(output_dir, f"{filename}.png")
            with open(filepath, 'wb') as f:
                f.write(image_data)
            print(f"✅ Successfully generated: {filename}.png")
            return True
        else:
            print(f"❌ Stability API error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating {filename}: {str(e)}")
        return False

def generate_image_free(prompt: str, filename: str, output_dir: str = "tarot_cards") -> bool:
    """Generate an image using free Pollinations API."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        encoded_prompt = requests.utils.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024"
        
        response = requests.get(image_url)
        if response.status_code == 200:
            filepath = os.path.join(output_dir, f"{filename}.png")
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"✅ Successfully generated: {filename}.png (via Pollinations)")
            return True
        else:
            print(f"❌ Failed to generate {filename}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating {filename}: {str(e)}")
        return False

def generate_image(prompt: str, filename: str, output_dir: str = "tarot_cards", method: str = "openai") -> bool:
    """Generate an image using the specified method."""
    if method == "openai":
        return generate_image_openai(prompt, filename, output_dir)
    elif method == "stability":
        return generate_image_stability(prompt, filename, output_dir)
    elif method == "free":
        return generate_image_free(prompt, filename, output_dir)
    else:
        print(f"❌ Unknown method: {method}")
        return False

def generate_all_major_arcana(delay_seconds: int = 2, method: str = "openai") -> None:
    """Generate images for all Major Arcana cards."""
    print("🔮 Starting Major Arcana Tarot Card Generation")
    print(f"📱 Using gpt model")
    print("=" * 50)
    
    successful = 0
    failed = 0
    
    for i, card in enumerate(MAJOR_ARCANA, 1):
        print(f"\n[{i}/22] Generating {card['name']} ({card['number']}) with gpt...")
        
        prompt = create_prompt(card['name'])
        success = generate_image(prompt, card['filename'], method=method)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        if i < len(MAJOR_ARCANA):
            print(f"⏳ Waiting {delay_seconds} seconds before next generation...")
            time.sleep(delay_seconds)
    
    print("\n" + "=" * 50)
    print("🎴 Generation Complete!")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Images saved in: ./tarot_cards/")

def generate_single_card(card_name: str, method: str = "openai") -> None:
    """Generate a single tarot card by name."""
    card = None
    for c in MAJOR_ARCANA:
        if c['name'].lower() == card_name.lower():
            card = c
            break
    
    if not card:
        print(f"❌ Card '{card_name}' not found in Major Arcana.")
        print("Available cards:")
        for i, c in enumerate(MAJOR_ARCANA, 1):
            print(f"  {i:2d}. {c['name']}")
        return
    
    prompt = create_prompt(card['name'])
    print(f"🔮 Generating {card['name']} using gpt...")
    success = generate_image(prompt, card['filename'], method=method)
    
    if success:
        print(f"✅ Successfully generated {card['name']}")
    else:
        print(f"❌ Failed to generate {card['name']}")

def select_single_card() -> str:
    """Interactive card selection."""
    print("\n🎴 Major Arcana Cards:")
    print("=" * 40)
    
    for i, card in enumerate(MAJOR_ARCANA, 1):
        print(f"  {i:2d}. {card['name']} ({card['number']})")
    
    while True:
        try:
            choice = input(f"\nEnter card number (1-{len(MAJOR_ARCANA)}) or card name: ").strip()
            
            if choice.isdigit():
                card_index = int(choice) - 1
                if 0 <= card_index < len(MAJOR_ARCANA):
                    return MAJOR_ARCANA[card_index]['name']
                else:
                    print(f"❌ Please enter a number between 1 and {len(MAJOR_ARCANA)}")
                    continue
            
            for card in MAJOR_ARCANA:
                if choice.lower() in card['name'].lower():
                    return card['name']
            
            print("❌ Card not found. Try again or use the number.")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            exit()
        except Exception:
            print("❌ Invalid input. Please try again.")

if __name__ == "__main__":
    print("🎴 Major Arcana Tarot Card Generator")
    print("=" * 50)
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OpenAI API key not found!")
        print("Please set your API key: export OPENAI_API_KEY='your-key-here'")
        exit()
    
    # Generation type selection
    print("What would you like to generate?")
    print("  1. Generate ALL 22 Major Arcana cards")
    print("  2. Generate a SINGLE card")
    
    while True:
        try:
            choice = input("\nEnter your choice (1 or 2): ").strip()
            
            if choice == "1":
                print(f"\n🚀 Generating all 22 Major Arcana cards...")
                confirm = input("Continue? (y/n): ").strip().lower()
                if confirm in ['y', 'yes']:
                    generate_all_major_arcana(delay_seconds=3, method="openai")
                else:
                    print("👋 Generation cancelled.")
                break
                
            elif choice == "2":
                selected_card = select_single_card()
                confirm = input(f"Generate '{selected_card}'? (y/n): ").strip().lower()
                if confirm in ['y', 'yes']:
                    generate_single_card(selected_card, method="openai")
                else:
                    print("👋 Generation cancelled.")
                break
                
            else:
                print("❌ Please enter 1 or 2")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            exit()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✨ Thank you for using the Tarot Card Generator!")