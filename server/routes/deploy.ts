import { Router } from "express";

const router = Router();

// Environment variables for GitHub API
const { GH_OWNER, GH_REPO, GH_TOKEN } = process.env;
const WORKFLOW_FILE = "deploy-api.yml"; // GitHub workflow file

router.post("/deploy", async (req, res) => {
  try {
    console.log("🚀 Deploy Backend request received");
    
    // Check required environment variables
    if (!GH_OWNER || !GH_REPO || !GH_TOKEN) {
      console.error("❌ Missing GitHub credentials");
      return res.status(500).json({ 
        success: false, 
        message: "Missing GitHub credentials (GH_OWNER, GH_REPO, GH_TOKEN)" 
      });
    }

    const dispatchUrl = `https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`;
    
    console.log(`📡 Dispatching workflow: ${dispatchUrl}`);
    
    const response = await fetch(dispatchUrl, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${GH_TOKEN}`,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "Glow-Nest-Deploy/1.0"
      },
      body: JSON.stringify({ 
        ref: "main",
        inputs: {
          environment: "production"
        }
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`❌ GitHub API error: ${response.status} ${errorText}`);
      return res.status(502).json({ 
        success: false, 
        message: `GitHub workflow dispatch failed: ${response.status} ${errorText}` 
      });
    }

    console.log("✅ GitHub workflow dispatched successfully");
    
    return res.json({ 
      success: true, 
      message: "Backend deployment workflow dispatched successfully",
      url: "https://glow-nest-api.fly.dev",
      status: "deploying",
      estimated_time: "2-3 minutes"
    });

  } catch (error: any) {
    console.error("💥 Deploy route error:", error);
    return res.status(500).json({ 
      success: false, 
      message: `Deploy error: ${error?.message || "Unknown error"}` 
    });
  }
});

export default router;
