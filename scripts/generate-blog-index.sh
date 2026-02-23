#!/bin/bash
# Generate blog-index.json from existing blog HTML files
# Run this after creating new blog posts

BLOG_DIR="public/blog"
OUTPUT_FILE="public/blog/blog-index.json"

echo "[" > "$OUTPUT_FILE"

first=true
for file in "$BLOG_DIR"/*.html; do
    # Skip index.html and non-post files
    if [[ "$(basename "$file")" == "index.html" ]] || [[ "$(basename "$file")" == *"methodology"* ]] || [[ "$(basename "$file")" == *"privacy"* ]]; then
        continue
    fi
    
    # Extract title from <title> tag
    title=$(grep -oP '(?<=<title>).*(?=</title>)' "$file" 2>/dev/null | head -1)
    
    # Get file modification date
    date=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1 || stat -f %Sm -t %Y-%m-%d "$file")
    
    filename=$(basename "$file")
    
    if [ -n "$title" ] && [ -n "$date" ]; then
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$OUTPUT_FILE"
        fi
        
        # Escape quotes in title
        title="${title//\"/\\\"}"
        
        echo "  {" >> "$OUTPUT_FILE"
        echo "    \"file\": \"$filename\"," >> "$OUTPUT_FILE"
        echo "    \"title\": \"$title\"," >> "$OUTPUT_FILE"
        echo "    \"date\": \"$date\"" >> "$OUTPUT_FILE"
        echo -n "  }" >> "$OUTPUT_FILE"
    fi
done

echo "" >> "$OUTPUT_FILE"
echo "]" >> "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE with $(grep -c '"file"' "$OUTPUT_FILE") posts"
