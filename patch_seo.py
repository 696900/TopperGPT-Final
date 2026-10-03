import os
import re

SEO_TITLE = "TopperGPT - AI Academic Workspace"
SEO_DESCRIPTION = (
    "Your syllabus. Your questions. Your AI study partner. From last-minute revision "
    "to deep concept learning, TopperGPT turns complex engineering topics into clear, "
    "exam-ready answers, smart notes, summaries, and practice questions. "
    "Don't just study harder. Study with TopperGPT."
)
SEO_KEYWORDS = (
    "TopperGPT, Mumbai University Engineering, MU C-Scheme, Engineering PYQs, "
    "Solved Question Papers, Smart Notes, Academic AI, Exam Preparation, "
    "Engineering Syllabus, Digital Circuits, Mechanics, Applied Mathematics"
)
SEO_IMAGE = "https://toppergpt.in/images/logo.jpeg"

def patch_streamlit_static_index():
    """
    Patches Streamlit's static index.html template so that search engine crawlers (Google, Bingbot, etc.)
    and social scrapers (WhatsApp, LinkedIn, Twitter/X, Discord, Facebook) read the official title,
    meta description, open graph preview image, and favicon instead of default Streamlit metadata.
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
            f'    <meta name="keywords" content="{SEO_KEYWORDS}" />\n'
            f'    <meta name="author" content="TopperGPT Inc." />\n'
            f'    <meta name="robots" content="index, follow" />\n'
            f'    <meta name="theme-color" content="#0B0F19" />\n'
            f'    <link rel="canonical" href="https://toppergpt.in" />\n'
            f'    <link rel="icon" type="image/jpeg" href="{SEO_IMAGE}" />\n'
            f'    <link rel="apple-touch-icon" href="{SEO_IMAGE}" />\n'
            f'    <meta property="og:title" content="{SEO_TITLE}" />\n'
            f'    <meta property="og:description" content="{SEO_DESCRIPTION}" />\n'
            f'    <meta property="og:type" content="website" />\n'
            f'    <meta property="og:url" content="https://toppergpt.in" />\n'
            f'    <meta property="og:site_name" content="TopperGPT" />\n'
            f'    <meta property="og:image" content="{SEO_IMAGE}" />\n'
            f'    <meta property="og:image:secure_url" content="{SEO_IMAGE}" />\n'
            f'    <meta property="og:image:type" content="image/jpeg" />\n'
            f'    <meta property="og:image:width" content="1200" />\n'
            f'    <meta property="og:image:height" content="630" />\n'
            f'    <meta property="og:image:alt" content="TopperGPT - AI Academic Workspace for Engineering Students" />\n'
            f'    <meta name="twitter:card" content="summary_large_image" />\n'
            f'    <meta name="twitter:title" content="{SEO_TITLE}" />\n'
            f'    <meta name="twitter:description" content="{SEO_DESCRIPTION}" />\n'
            f'    <meta name="twitter:image" content="{SEO_IMAGE}" />\n'
            f'    <meta name="twitter:image:alt" content="TopperGPT - AI Academic Workspace" />'
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
