import os
import re

SEO_TITLE = "TopperGPT - AI Academic Workspace"
SEO_DESCRIPTION = (
    "Your syllabus. Your questions. Your AI study partner. From last-minute revision "
    "to deep concept learning, TopperGPT turns complex engineering topics into clear, "
    "exam-ready answers, smart notes, summaries, and practice questions. "
    "Don't just study harder. Study with TopperGPT."
)

def patch_streamlit_static_index():
    """
    Patches Streamlit's static index.html template so that search engine crawlers (Google, Bingbot, etc.)
    and social scrapers read the official title and meta description instead of the default
    'Streamlit. You need to enable JavaScript to run this app.'
    """
    try:
        import streamlit
        static_dir = os.path.join(os.path.dirname(streamlit.__file__), "static")
        index_file = os.path.join(static_dir, "index.html")

        if not os.path.exists(index_file):
            return False

        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()

        seo_meta = (
            f"<title>{SEO_TITLE}</title>\n"
            f'    <meta name="description" content="{SEO_DESCRIPTION}" />\n'
            f'    <meta name="robots" content="index, follow" />\n'
            f'    <meta property="og:title" content="{SEO_TITLE}" />\n'
            f'    <meta property="og:description" content="{SEO_DESCRIPTION}" />\n'
            f'    <meta property="og:type" content="website" />\n'
            f'    <meta property="og:url" content="https://toppergpt.in" />\n'
            f'    <meta name="twitter:card" content="summary_large_image" />\n'
            f'    <meta name="twitter:title" content="{SEO_TITLE}" />\n'
            f'    <meta name="twitter:description" content="{SEO_DESCRIPTION}" />'
        )

        modified = False

        if "<title>Streamlit</title>" in content:
            content = content.replace("<title>Streamlit</title>", seo_meta)
            modified = True
        elif 'name="description"' not in content:
            if "<title>" in content:
                content = re.sub(r"<title>.*?</title>", seo_meta, content, flags=re.DOTALL)
            else:
                content = content.replace("<head>", f"<head>\n    {seo_meta}")
            modified = True

        # Clean out default Streamlit noscript snippet
        noscript_seo = (
            f"<noscript>\n"
            f"      <h1>{SEO_TITLE}</h1>\n"
            f"      <p>{SEO_DESCRIPTION}</p>\n"
            f"    </noscript>"
        )
        if "<noscript>You need to enable JavaScript to run this app.</noscript>" in content:
            content = content.replace(
                "<noscript>You need to enable JavaScript to run this app.</noscript>",
                noscript_seo
            )
            modified = True

        if modified:
            with open(index_file, "w", encoding="utf-8") as f:
                f.write(content)

        # Update static favicon if custom logo exists
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "images", "logo.jpeg")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(base_dir, "logo.jpeg")

        if os.path.exists(logo_path):
            fav_dest = os.path.join(static_dir, "favicon.png")
            try:
                from PIL import Image
                im = Image.open(logo_path).convert("RGBA")
                im.save(fav_dest, "PNG")
            except Exception:
                pass

        return True
    except Exception as e:
        print(f"Notice: SEO patch skipped: {e}")
        return False

def patch_all():
    return patch_streamlit_static_index()

if __name__ == "__main__":
    success = patch_all()
    print("SEO patch completed:", success)
