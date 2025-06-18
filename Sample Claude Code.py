def analyze_briefs_with_claude(brief_paths_and_descriptions, case_number, prior_issues=None):
    """Analyze multiple legal brief PDFs with Claude to extract legal issues"""
    try:
        # Get API key from environment variable
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not found in .env file")
            return []
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Prepare content array with all briefs
        content = []
        brief_descriptions = []
        
        # Read all PDF files and add them to content
        import base64
        for brief_path, brief_description in brief_paths_and_descriptions:
            try:
                with open(brief_path, 'rb') as f:
                    pdf_content = base64.b64encode(f.read()).decode('utf-8')
                
                content.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_content
                    }
                })
                brief_descriptions.append(brief_description)
            except Exception as e:
                print(f"    ⚠️  Error reading {brief_path}: {e}")
                continue
        
        if not content:
            print(f"    ⚠️  No valid briefs to analyze for {case_number}")
            return []
        
        # Create the analysis prompt
        brief_list = "\n".join([f"- {desc}" for desc in brief_descriptions])
        
        # Build prompt based on whether we have prior issues
        if prior_issues and len(prior_issues) > 0:
            # Format prior issues for Claude
            prior_issues_text = "\n".join([
                f"- {issue.get('legal_area', 'General')}: {issue.get('description', 'No description')}"
                for issue in prior_issues
            ])
            
            prompt_text = f"""You are a legal expert analyzing criminal appellate briefs from Texas courts. 

CONTEXT: I have already analyzed some briefs for case {case_number} and identified the following legal issues:

PREVIOUSLY IDENTIFIED ISSUES:
{prior_issues_text}

NEW BRIEFS TO ANALYZE:
{brief_list}

TASK: Please analyze these NEW briefs and determine:
1. What NEW legal issues are raised that were NOT in the previous analysis
2. What CHANGES or ADDITIONS to existing issues are made by these new briefs
3. Consolidate similar issues and avoid duplicating issues already identified

For each NEW or CHANGED issue, provide:
1. A concise description of the issue (1-2 sentences)
2. The specific legal area (e.g., "Fourth Amendment Search and Seizure", "Ineffective Assistance of Counsel", "Sufficiency of Evidence", etc.)
3. Which brief(s) raised this issue
4. Whether this is "new" or "expanded" (if it adds detail to an existing issue)

Focus on substantive legal arguments, not procedural matters. Return your analysis in JSON format:

{{
  "issues": [
    {{
      "description": "Brief description of the legal issue",
      "legal_area": "Specific area of law",
      "source_briefs": ["brief description 1", "brief description 2"],
      "status": "new" or "expanded"
    }}
  ]
}}"""
        else:
            # First batch - analyze normally
            prompt_text = f"""You are a legal expert analyzing criminal appellate briefs from Texas courts. Please analyze ALL the briefs provided for case {case_number} and identify the distinct legal issues raised across all briefs.

The briefs included are:
{brief_list}

For each legal issue, provide:
1. A concise description of the issue (1-2 sentences)
2. The specific legal area (e.g., "Fourth Amendment Search and Seizure", "Ineffective Assistance of Counsel", "Sufficiency of Evidence", etc.)
3. Which brief(s) raised this issue

Focus on substantive legal arguments, not procedural matters. Consolidate similar issues from different briefs. Return your analysis in JSON format with an array of issues:

{{
  "issues": [
    {{
      "description": "Brief description of the legal issue",
      "legal_area": "Specific area of law",
      "source_briefs": ["brief description 1", "brief description 2"]
    }}
  ]
}}"""
        
        content.append({
            "type": "text",
            "text": prompt_text
        })
        
        # Create message with all PDF attachments
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )
        
        response_text = message.content[0].text
        
        # Parse JSON response using enhanced parser
        return parse_claude_json_response(response_text, case_number)
            
    except Exception as e:
        error_msg = str(e)
        print(f"    ⚠️  Error analyzing briefs with Claude for {case_number}: {error_msg}")
        
        # Check if it's a rate limit error
        if "429" in error_msg or "rate_limit_error" in error_msg.lower() or "rate limit" in error_msg.lower():
            print(f"    🛑 Rate limit exceeded for {case_number}. Backing off...")
            import time
            # Wait 60 seconds before retrying
            print(f"    ⏰ Waiting 60 seconds before continuing...")
            time.sleep(60)
            print(f"    🔄 Resuming analysis after rate limit backoff...")
            return None  # Signal to retry or skip for now
        
        # Check if it's a PDF processing error
        if "could not process pdf" in error_msg.lower() or "pdf" in error_msg.lower():
            print(f"    🔄 PDF processing error for batch, will try individual briefs...")
            return "PROCESS_INDIVIDUALLY"  # Signal to process briefs individually
        
        # Check if it's a size limit error (various error messages)
        size_limit_keywords = ["too large", "limit", "size", "100 pdf pages", "maximum", "exceeded"]
        if any(keyword in error_msg.lower() for keyword in size_limit_keywords):
            print(f"    🔄 Input too large, falling back to smaller groups...")
            return None  # Signal to fallback to smaller processing
        
        return []

