#!/bin/bash
# Generate blog-index.json from Eleventy output (subdirectories)
# Run this after creating new blog posts

BLOG_DIR="_site/blog"
OUTPUT_FILE="_site/blog/blog-index.json"

# First pass: collect all posts
TMP_FILE=$(mktemp)

first=true
for file in "$BLOG_DIR"/2026-*/index.html; do
    # Skip non-post files
    if [[ "$(basename "$(dirname "$file")")" == *"methodology"* ]] || [[ "$(basename "$(dirname "$file")")" == *"privacy"* ]]; then
        continue
    fi
    
    # Extract title from <title> tag
    title=$(grep -oP '(?<=<title>).*(?=</title>)' "$file" 2>/dev/null | head -1)
    
    # Extract date from directory name (2026-03-18-...)
    dir=$(basename "$(dirname "$file")")
    date=$(echo "$dir" | grep -oP '^\d{4}-\d{2}-\d{2}' 2>/dev/null)
    
    if [ -n "$title" ] && [ -n "$date" ]; then
        # Escape quotes in title
        title="${title//\"/\\\"}"
        echo "$date|$title|$dir/index.html" >> "$TMP_FILE"
    fi
done

# Sort by date (newest first) and generate JSON
echo "[" > "$OUTPUT_FILE"

if [ -f "$TMP_FILE" ]; then
    sorted=$(cat "$TMP_FILE" | sort -r)
    
    first=true
    while IFS='|' read -r date title file; do
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$OUTPUT_FILE"
        fi
        
        echo "  {" >> "$OUTPUT_FILE"
        echo "    \"file\": \"$file\"," >> "$OUTPUT_FILE"
        echo "    \"title\": \"$title\"," >> "$OUTPUT_FILE"
        echo "    \"date\": \"$date\"" >> "$OUTPUT_FILE"
        echo -n "  }" >> "$OUTPUT_FILE"
    done <<< "$sorted"
fi

echo "" >> "$OUTPUT_FILE"
echo "]" >> "$OUTPUT_FILE"

rm -f "$TMP_FILE"

echo "Generated $OUTPUT_FILE with $(grep -c '"file"' "$OUTPUT_FILE") posts"
