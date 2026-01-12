from js import Response, fetch, JSON, Headers

async def on_fetch(request, env):
    """
    Cloudflare Python Worker Entry Point
    """
    # CORS Headers
    headers = Headers.new()
    headers.append("Access-Control-Allow-Origin", "*") # In production, restrict this
    headers.append("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    headers.append("Access-Control-Allow-Headers", "Content-Type")

    # Handle OPTIONS (Preflight)
    if request.method == "OPTIONS":
        return Response.new(None, headers=headers)

    url = request.url
    
    # Simple Router
    if url.endswith("/api/health"):
        return Response.new("OK", headers=headers)
        
    elif url.endswith("/api/analyze"):
        if request.method != "POST":
            return Response.new("Method Not Allowed", status=405, headers=headers)
        
        try:
            req_json = await request.json()
            # TODO: Call Gemini API using env.GEMINI_API_KEY
            # For now, return a mock response to prove connectivity
            
            mock_response = {
                "status": "success",
                "analysis": "[BACKEND GENERATED] Analysis complete based on secure logic."
            }
            return Response.new(JSON.stringify(mock_response), headers=headers)
        except Exception as e:
            return Response.new(f"Error: {str(e)}", status=500, headers=headers)

    return Response.new("Not Found", status=404, headers=headers)
