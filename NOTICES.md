# Legal Notices - LLM Search Scout

## License Summary

This Docker image contains software under multiple licenses:

### LLM Search Scout API (MIT License)
- **License**: MIT
- **Copyright**: (c) 2024 Joseph Volmer and LLM Search Scout Contributors
- **Source Code**: https://github.com/josephvolmer/llm-search-scout
- **Components**: FastAPI wrapper, content extraction, metadata enrichment, citation formatting

### SearXNG (AGPL-3.0 License)
- **License**: GNU Affero General Public License v3.0 (AGPL-3.0)
- **Copyright**: SearXNG Contributors
- **Source Code**: https://github.com/searxng/searxng
- **Container Path**: `/usr/local/searxng`
- **Modifications**: None - used unmodified as cloned from official repository
- **Full License**: https://github.com/searxng/searxng/blob/master/LICENSE

## AGPL-3.0 Source Code Availability

In compliance with AGPL-3.0 Section 6, the complete source code for SearXNG is included within this Docker image at `/usr/local/searxng`. You can access it by:

```bash
# Access source code inside running container
docker run -it josephvolmer/llm-search-scout /bin/bash
cd /usr/local/searxng
ls -la

# Or inspect from outside
docker cp <container-id>:/usr/local/searxng ./searxng-source
```

Or clone the original repository:
```bash
git clone https://github.com/searxng/searxng.git
```

## AGPL-3.0 Section 13 Applicability

**AGPL Section 13 does NOT apply to this distribution** because:
1. SearXNG is used **unmodified** (installed via `git clone` in Dockerfile)
2. No changes have been made to SearXNG source code
3. Section 13 only triggers when you modify AGPL-licensed software

## Architecture and License Separation

This Docker image contains two separate programs that communicate over HTTP:

```
┌─────────────────────────────────────┐
│  LLM Search Scout API (MIT)         │  ← Your interaction point
│  FastAPI + Content Processing       │
└──────────────┬──────────────────────┘
               │ HTTP/JSON API
┌──────────────▼──────────────────────┐
│  SearXNG Service (AGPL-3.0)         │  ← Internal search engine
│  Unmodified, separate process       │
└─────────────────────────────────────┘
```

**Key Points:**
- The MIT-licensed API wrapper and AGPL-licensed SearXNG are **separate programs**
- They communicate via a standard HTTP interface
- No derivative work or linking relationship exists
- Each component retains its original license
- Using the MIT API does not impose AGPL obligations on your code

## Additional Dependencies

See [THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES) for complete license texts of all dependencies including:
- FastAPI (MIT)
- BeautifulSoup4 (MIT)
- lxml (BSD-3-Clause)
- readability-lxml (Apache 2.0)
- Other Python packages (see `api/requirements.txt`)

## Compliance Statement

This project complies with all applicable open source licenses:

1. **SearXNG (AGPL-3.0)**: Distributed unmodified with complete source code included in the container
2. **LLM Search Scout API (MIT)**: Original code licensed under MIT, does not create a derivative work of SearXNG
3. **Third-party libraries**: All dependencies properly attributed with licenses documented

## User Obligations

### If you use this Docker image as-is:
- ✅ No additional obligations beyond SearXNG's AGPL-3.0 for that component
- ✅ The MIT-licensed API wrapper can be used freely
- ✅ You do NOT need to open-source your code that uses the API

### If you modify SearXNG:
- ⚠️ AGPL Section 13 applies - you must offer modified source to network users
- ⚠️ You must preserve AGPL-3.0 license and attribution
- ⚠️ Modified versions must be clearly marked

### If you modify the LLM Search Scout API:
- ✅ MIT license allows free modification
- ✅ You must include MIT license and copyright notice
- ✅ No obligation to share modifications (MIT is permissive)

## Questions?

For license compliance questions or concerns:
- **General**: Open an issue at https://github.com/josephvolmer/llm-search-scout/issues
- **SearXNG**: See https://github.com/searxng/searxng
- **Legal Advice**: Consult an attorney specializing in open source licensing

## Disclaimer

This notice is provided for informational purposes. For authoritative license information, refer to the LICENSE and THIRD_PARTY_LICENSES files, as well as the original license texts from each component's source repository.

---

**Last Updated**: November 2024
**Image Version**: 1.0.0
