from js import Response, fetch, JSON, Headers

async def on_fetch(request, env):
    """
    Cloudflare Python Worker Entry Point - Pure Logic
    """
    # CORS Headers
    headers = Headers.new()
    headers.append("Access-Control-Allow-Origin", "https://schemabio.com")
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
            req_js = await request.json()
            # Convert JS Object to Python Dictionary to use .get()
            req_data = req_js.to_py()
            
            # Extract data safely
            email = req_data.get("email")
            interest = req_data.get("interest")
            primary_challenge = req_data.get("primary_challenge")
            source = req_data.get("source", "unknown")
            user_agent = req_data.get("userAgent", request.headers.get("User-Agent"))

            if not email:
                 return Response.new(JSON.stringify({"error": "Email is required"}), status=400, headers=headers)

            # Insert into D1 Database
            # Python Workers access bindings via `env`
            stmt = env.DB.prepare("""
                INSERT INTO leads (email, interest, primary_challenge, source, user_agent) 
                VALUES (?, ?, ?, ?, ?)
            """)
            
            # Execute
            await stmt.bind(email, interest, primary_challenge, source, user_agent).run()
            
            response_data = {
                "status": "success",
                "message": "Data saved successfully",
                "timestamp": "server-time" 
            }
            return Response.new(JSON.stringify(response_data), headers=headers)
        except Exception as e:
            # Enhanced Error Logging
            import traceback
            error_details = traceback.format_exc()
            print(f"Server Error: {error_details}") # Log to Cloudflare Dashboard
            return Response.new(f"Error: {str(e)}", status=500, headers=headers)

    return Response.new("Not Found", status=404, headers=headers)