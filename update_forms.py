import os
import re

template_dir = r"e:\jayam_ai_insurance\templates"
files_to_update = [
    "bike_details.html", "car_details.html", "pcv_details.html", 
    "gcv_details.html", "misc_details.html", "health_details.html", 
    "life_details.html", "corporate_details.html", "motor_selection.html", 
    "enquiry.html", "services.html", "selection.html", "confirmation.html", 
    "success.html"
]

for filename in files_to_update:
    filepath = os.path.join(template_dir, filename)
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 1. Strip <style>...</style> block
    content = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL)
    
    # 2. Add header include
    if "{% include 'header.html' %}" not in content:
        # Try to replace existing exact header pattern
        header_pattern = r'<header>.*?</header>'
        if re.search(header_pattern, content, flags=re.DOTALL):
            content = re.sub(header_pattern, "{% include 'header.html' %}", content, count=1, flags=re.DOTALL)
        else:
            # Or inject after <body>
            content = re.sub(r'<body.*?>', r'\g<0>\n    {% include \'header.html\' %}', content, count=1)
            
    # 3. Add footer include
    if "{% include 'footer.html' %}" not in content:
        content = re.sub(r'</body>', r'    {% include \'footer.html\' %}\n</body>', content)
        
    # 4. Make sure style.css is linked properly (not style.css but {{ url_for('static', filename='css/style.css') }})
    if "filename='css/style.css'" not in content:
        content = re.sub(r'<link rel="stylesheet" href=".*?style\.css".*?>', 
                         r'<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/style.css\') }}">', content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Template standardization complete.")
