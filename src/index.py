from js import Response, fetch, JSON, Headers

async def on_fetch(request, env):
    """
    Cloudflare Python Worker Entry Point - Pure Logic
    """
    # CORS Headers
    headers = Headers.new()
    headers.append("Access-Control-Allow-Origin", "*")
    headers.append("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    headers.append("Access-Control-Allow-Headers", "Content-Type")

    # Handle OPTIONS (Preflight)
    if request.method == "OPTIONS":
        return Response.new(None, headers=headers)

    url = request.url
    
    # Health Check
    if url.endswith("/api/health"):
        return Response.new("System Online", headers=headers)
        
    # Data Ingestion Endpoint
    elif url.endswith("/api/submit"):
        if request.method != "POST":
            return Response.new("Method Not Allowed", status=405, headers=headers)
        
        try:
            req_json = await request.json()
            # In a real scenario, we would validate and store this data
            # For now, we just acknowledge receipt
            
            response_data = {
                "status": "success",
                "message": "Data received",
                "timestamp": "server-time" 
            }
            return Response.new(JSON.stringify(response_data), headers=headers)
        except Exception as e:
            return Response.new(f"Error: {str(e)}", status=500, headers=headers)

    return Response.new("Not Found", status=404, headers=headers)