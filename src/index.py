from js import Response, fetch, JSON, Headers

async def on_fetch(request, env):
    """
    Cloudflare Python Worker Entry Point - Pure Logic
    """
    # CORS Headers
    headers = Headers.new()
    headers.append("Access-Control-Allow-Origin", "https://schemabio.com")
    headers.append("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    headers.append("Access-Control-Allow-Headers", "Content-Type, Authorization")

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
            # Convert to Python dict for stable access
            req_data = req_js.to_py() if hasattr(req_js, "to_py") else dict(req_js)
            
            # Rigorous field extraction with fallback to empty string
            # This ensures no JavaScript 'undefined' value is passed to D1
            email = req_data.get("email")
            interest = req_data.get("interest") if req_data.get("interest") is not None else ""
            primary_challenge = req_data.get("primary_challenge") if req_data.get("primary_challenge") is not None else ""
            source = req_data.get("source") if req_data.get("source") is not None else "landing_page_mvp"
            
            # UA Handling
            ua_val = req_data.get("userAgent")
            if ua_val is None:
                ua_val = request.headers.get("User-Agent")
            if ua_val is None:
                ua_val = ""
            user_agent = str(ua_val)

            if not email:
                 return Response.new(JSON.stringify({"error": "Email is required"}), status=400, headers=headers)

            # Insert into D1 Database
            stmt = env.DB.prepare("""
                INSERT INTO leads (email, interest, primary_challenge, source, user_agent) 
                VALUES (?, ?, ?, ?, ?)
            """)
            
            # Passing 5 guaranteed string objects
            await stmt.bind(email, interest, primary_challenge, source, user_agent).run()
            
            import json
            response_data = {"status": "success", "message": "Data saved"}
            return Response.new(json.dumps(response_data), headers=headers)
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"CRITICAL_ERROR: {error_msg}")
            return Response.new(f"Error: {str(e)}", status=500, headers=headers)

    # Admin Endpoint: Fetch Leads
    elif url.endswith("/api/admin/leads"):
        # 1. Method Check
        if request.method != "GET":
             return Response.new("Method Not Allowed", status=405, headers=headers)
        
        # 2. Security Check (Bearer Token)
        auth_header = request.headers.get("Authorization")
        # env.ADMIN_SECRET MUST be set in Cloudflare Dashboard / .dev.vars
        admin_secret = getattr(env, "ADMIN_SECRET", None)
        
        if not admin_secret or not auth_header or auth_header != f"Bearer {admin_secret}":
            return Response.new(JSON.stringify({"error": "Unauthorized"}), status=401, headers=headers)

        try:
            # 3. Query D1
            stmt = env.DB.prepare("SELECT * FROM leads ORDER BY created_at DESC LIMIT 100")
            results = await stmt.all()
            
            # 4. Serialize
            import json
            # D1 results.results is a list of dicts (in Python worker) or PyProxy
            # We need to convert safely if it's a proxy, but usually stmt.all() returns a Python-friendly object structure in newer workers.
            # However, safer to handle serialization carefully.
            
            data = results.results # This is the list of rows
            
            # If data is a JsProxy, convert it. If it's already a list, this is fine.
            if hasattr(data, "to_py"):
                data = data.to_py()
                
            return Response.new(json.dumps(data), headers=headers)
            
        except Exception as e:
            import traceback
            print(f"Admin Error: {traceback.format_exc()}")
            return Response.new(f"Database Error: {str(e)}", status=500, headers=headers)

    return Response.new("Not Found", status=404, headers=headers)