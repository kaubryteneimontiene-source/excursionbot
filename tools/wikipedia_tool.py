import wikipedia
from langchain_core.tools import tool

wikipedia.set_lang("en")

BALTIC_COUNTRIES = ["Lithuania", "Latvia", "Estonia"]

@tool
def search_site_wikipedia(site_name: str) -> str:
    """
    Search Wikipedia for information about a Baltic historical or cultural site.
    Use this tool when the user asks about a site that may not be in the
    local knowledge base, or when they need broader information about
    any Lithuanian, Latvian, or Estonian historical site or attraction.

    Args:
        site_name: Name of the historical site, city, or attraction to search

    Returns:
        A summary of the site from Wikipedia, or an error message
    """
    try:
        # Search Wikipedia
        search_results = wikipedia.search(f"{site_name} Baltic", results=3)

        if not search_results:
            search_results = wikipedia.search(site_name, results=3)

        if not search_results:
            return f"No Wikipedia information found for '{site_name}'."

        # Try to get the most relevant page
        for result in search_results:
            try:
                page = wikipedia.page(result, auto_suggest=False)

                # Check if the page is related to Baltic region or the site
                content_lower = page.content.lower()
                site_lower = site_name.lower()

                is_relevant = (
                    any(country.lower() in content_lower for country in BALTIC_COUNTRIES)
                    or site_lower in content_lower
                    or site_lower in page.title.lower()
                )

                if is_relevant:
                    # Return first 1500 characters — enough for RAG context
                    summary = page.content[:1500]
                    return (
                        f"📖 Wikipedia: {page.title}\n"
                        f"🔗 Source: {page.url}\n\n"
                        f"{summary}\n\n"
                        f"[Source: Wikipedia — always verify with official site]"
                    )

            except wikipedia.exceptions.DisambiguationError as e:
                # If ambiguous, try the first option
                try:
                    page = wikipedia.page(e.options[0], auto_suggest=False)
                    summary = page.content[:1500]
                    return (
                        f"📖 Wikipedia: {page.title}\n"
                        f"🔗 Source: {page.url}\n\n"
                        f"{summary}\n\n"
                        f"[Source: Wikipedia — always verify with official site]"
                    )
                except Exception:
                    continue
            except Exception:
                continue

        return (
            f"Found search results for '{site_name}' but could not retrieve "
            f"a relevant Wikipedia page. Try a more specific name."
        )

    except Exception as e:
        return f"Wikipedia search error: {str(e)}. Please try again."
