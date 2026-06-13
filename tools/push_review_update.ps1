param(
  [string]$Message = "Prepare TikTok review and upload workflow"
)

$ErrorActionPreference = "Stop"

$files = @(
  ".env.example",
  "README.md",
  "docs_tiktok_oauth_readme.md",
  "src_pipeline.py",
  "src_tiktok_oauth.py",
  "src_tiktok_publisher.py",
  "src_agents.py",
  "src_approval_queue.py",
  "src_growth_memory.py",
  "src_launch_check.py",
  "src_content_planner.py",
  "src_script_check.py",
  ".agents/vulgascience_agents.json",
  "content/production_queue.json",
  "content/templates/vulgascience_video_schema.json",
  "content/scripts/dopamine_prediction_reward.json",
  "docs/index.html",
  "docs/callback.html",
  "docs/terms.html",
  "docs/privacy.html",
  "docs/tiktok_growth_playbook.md",
  "docs/review_waiting_plan.md",
  "docs/next_video_batch.md",
  "tools/build_tiktok_review_assets.py",
  "tools/push_review_update.ps1"
)

git add -- $files
git status --short
git commit -m $Message
git push origin main
