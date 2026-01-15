#!/bin/sh

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛠  LOADING PLUGINS..."

PLUGIN_COUNT=0

for file in plugins/*.py; do
    if [ -f "$file" ]; then
        NAME=$(basename "$file")
        case "$NAME" in
            __*) ;;
            *)
                echo "✅ Successfully Loaded: $NAME"
                PLUGIN_COUNT=$((PLUGIN_COUNT+1))
            ;;
        esac
    fi
done

echo "🎉 Total $PLUGIN_COUNT Plugins Loaded!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Bot start
python bot.py
