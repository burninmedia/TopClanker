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
    
    # Extract date from YAML frontmatter (date: "2026-03-07") or meta date
    date=$(grep -oP 'date:\s*"[^"]+"' "$file" 2>/dev/null | head -1 | sed 's/date:\s*"\([^"]*\)"/\1/')
    
    # Also try meta name="date" 
    if [ -z "$date" ]; then
        date=$(grep -oP 'name="date"\s+content="[^"]+"' "$file" 2>/dev/null | sed 's/.*content="\([^"]*\)"/\1/')
    fi
    
    # Try to extract date from filename (2026-03-01-...)
    if [ -z "$date" ]; then
        filename=$(basename "$file")
        date=$(echo "$filename" | grep -oP '^\d{4}-\d{2}-\d{2}' 2>/dev/null)
    fi
    
    # Fallback to file modification date if no date found
    if [ -z "$date" ]; then
        date=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1 || stat -f %Sm -t %Y-%m-%d "$file")
    fi
    
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
