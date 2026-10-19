#!/usr/bin/env python3
"""
Portfolio Studio: Local Content Management & GitHub Pages Publisher
for Syed Emad Uddin Shubha (https://syedshubha.github.io)

Zero-dependency Python 3 application serving:
  - http://127.0.0.1:8090/studio     -> Interactive GUI to add/edit Memes, Blog Posts,
                                        Publications, News Updates, and Files/CV,
                                        plus 1-click Git commit & push to GitHub Pages.
  - http://127.0.0.1:8090/index.html -> Live local preview of the entire portfolio site.
"""

import base64
import json
import os
import re
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_JSON = os.path.join(REPO_DIR, "data", "portfolio_data.json")
DATA_JS = os.path.join(REPO_DIR, "data", "portfolio_data.js")
IMAGES_DIR = os.path.join(REPO_DIR, "images")
FILES_DIR = os.path.join(REPO_DIR, "assets", "files")
CV_PATH = os.path.join(REPO_DIR, "assets", "Curriculum_Vitae_Syed_Emad_Uddin_Shubha.pdf")
PORT = 8090


def load_portfolio_data():
    with open(DATA_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_portfolio_data(data):
    os.makedirs(os.path.dirname(DATA_JSON), exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False)
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    with open(DATA_JS, "w", encoding="utf-8") as f:
        f.write("window.PORTFOLIO_DATA = " + text + ";\n")


def sanitize_filename(name):
    name = os.path.basename(name.strip())
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name or ("upload_" + str(int(time.time())))


def run_git_command(args):
    res = subprocess.run(
        ["git"] + args,
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
    )
    return res.returncode, (res.stdout + "\n" + res.stderr).strip()


STUDIO_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Portfolio Studio: Local Manager | Syed Emad Uddin Shubha</title>
<link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --navy-950: #0a1120;
    --navy-900: #0f172a;
    --navy-800: #1e293b;
    --blue: #1d4ed8;
    --blue-light: #eff6ff;
    --gold: #d97706;
    --green: #15803d;
    --red: #b91c1c;
    --bg: #f1f5f9;
    --card: #ffffff;
    --border: #cbd5e1;
    --text: #0f172a;
    --muted: #475569;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); line-height: 1.5; }
  header {
    background: linear-gradient(135deg, #0a1120 0%, #172554 60%, #3b0764 100%);
    color: #fff;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 3px solid #f59e0b;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  header h1 { font-family: 'Crimson Pro', serif; font-size: 1.55rem; }
  header p { font-size: 0.8rem; color: #cbd5e1; }
  .top-actions { display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap; }
  .btn {
    padding: 0.52rem 1rem;
    border-radius: 7px;
    border: 1px solid transparent;
    font-size: 0.84rem;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    text-decoration: none;
    transition: all 0.15s;
  }
  .btn-primary { background: var(--blue); color: #fff; }
  .btn-primary:hover { background: #1e40af; }
  .btn-gold { background: #f59e0b; color: #0f172a; }
  .btn-gold:hover { background: #fbbf24; }
  .btn-outline { background: rgba(255,255,255,0.12); color: #fff; border-color: rgba(255,255,255,0.25); }
  .btn-outline:hover { background: rgba(255,255,255,0.22); }
  .btn-light { background: #f8fafc; color: var(--navy-900); border-color: var(--border); }
  .btn-light:hover { background: #e2e8f0; }
  .btn-danger { background: #fee2e2; color: var(--red); border-color: #fecaca; }
  .btn-danger:hover { background: #fecaca; }

  .layout {
    max-width: 1320px;
    margin: 1.5rem auto;
    padding: 0 1.5rem 4rem;
    display: grid;
    grid-template-columns: 230px 1fr;
    gap: 1.5rem;
  }
  .sidebar {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.85rem;
    height: fit-content;
    position: sticky;
    top: 84px;
  }
  .tab-btn {
    width: 100%;
    text-align: left;
    padding: 0.7rem 0.9rem;
    border: none;
    background: transparent;
    border-radius: 7px;
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--muted);
    cursor: pointer;
    margin-bottom: 0.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .tab-btn:hover { background: #f1f5f9; color: var(--text); }
  .tab-btn.active { background: var(--navy-900); color: #fff; }
  .badge {
    font-size: 0.72rem;
    padding: 0.1rem 0.45rem;
    border-radius: 99px;
    background: rgba(255,255,255,0.18);
  }
  .tab-btn:not(.active) .badge { background: #e2e8f0; color: var(--navy-800); }

  .panel { display: none; }
  .panel.active { display: block; }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 3px rgba(15,23,42,0.05);
  }
  .card h2 { font-family: 'Crimson Pro', serif; font-size: 1.45rem; margin-bottom: 0.35rem; }
  .card-sub { font-size: 0.86rem; color: var(--muted); margin-bottom: 1.15rem; }

  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
  .form-group { display: flex; flex-direction: column; gap: 0.35rem; margin-bottom: 0.9rem; }
  label { font-size: 0.8rem; font-weight: 600; color: var(--navy-800); }
  input[type=text], input[type=url], select, textarea {
    padding: 0.58rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-family: inherit;
    font-size: 0.88rem;
    width: 100%;
  }
  textarea { resize: vertical; min-height: 90px; }

  .dropzone {
    border: 2px dashed #94a3b8;
    border-radius: 8px;
    padding: 1.1rem;
    text-align: center;
    background: #f8fafc;
    cursor: pointer;
    transition: all 0.15s;
  }
  .dropzone:hover { border-color: var(--blue); background: var(--blue-light); }

  .item-list { display: flex; flex-direction: column; gap: 0.75rem; }
  .item-row {
    display: flex;
    gap: 1rem;
    align-items: center;
    padding: 0.85rem 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #f8fafc;
  }
  .item-thumb {
    width: 68px;
    height: 68px;
    object-fit: contain;
    background: #0f172a;
    border-radius: 6px;
    flex-shrink: 0;
  }
  .item-info { flex: 1; min-width: 0; }
  .item-info h4 { font-size: 0.96rem; color: var(--navy-900); margin-bottom: 0.15rem; }
  .item-info p { font-size: 0.8rem; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .item-actions { display: flex; gap: 0.4rem; flex-shrink: 0; }

  #statusBanner {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: var(--navy-900);
    color: #fff;
    padding: 0.85rem 1.25rem;
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.25);
    display: none;
    z-index: 999;
    max-width: 460px;
    font-size: 0.86rem;
  }
</style>
</head>
<body>

<header>
  <div>
    <h1>🎓 Portfolio Studio: Syed Emad Uddin Shubha</h1>
    <p>Local Desktop Manager for Memes, Blog Posts, Publications, News & One-Click GitHub Pages Sync</p>
  </div>
  <div class="top-actions">
    <a href="/index.html" target="_blank" class="btn btn-outline">🌐 Preview Main Site ↗</a>
    <a href="/blog.html" target="_blank" class="btn btn-outline">✍️ Preview Blog ↗</a>
    <a href="/memes.html" target="_blank" class="btn btn-outline">🎭 Preview Memes ↗</a>
    <button class="btn btn-primary" onclick="saveDataOnly()">💾 Save Local</button>
    <button class="btn btn-gold" onclick="saveAndPushGitHub()">🚀 Save & Publish to GitHub</button>
  </div>
</header>

<div class="layout">
  <aside class="sidebar">
    <button class="tab-btn active" onclick="switchTab('memes', this)">
      <span>🎭 Memes Gallery</span>
      <span class="badge" id="countMemes">0</span>
    </button>
    <button class="tab-btn" onclick="switchTab('posts', this)">
      <span>✍️ Blog & Essays</span>
      <span class="badge" id="countPosts">0</span>
    </button>
    <button class="tab-btn" onclick="switchTab('pubs', this)">
      <span>📚 Publications</span>
      <span class="badge" id="countPubs">0</span>
    </button>
    <button class="tab-btn" onclick="switchTab('updates', this)">
      <span>📢 News & Updates</span>
      <span class="badge" id="countUpdates">0</span>
    </button>
    <button class="tab-btn" onclick="switchTab('files', this)">
      <span>📁 CV & Files Upload</span>
    </button>
    <button class="tab-btn" onclick="switchTab('git', this)">
      <span>🚀 GitHub Sync Status</span>
    </button>
  </aside>

  <main>
    <!-- 1. MEMES PANEL -->
    <section class="panel active" id="panel-memes">
      <div class="card">
        <h2 id="memeFormHeader">➕ Add New Science / Philosophy Meme</h2>
        <p class="card-sub">Upload a meme image from your computer, write its caption and technical explanation, and it will appear at the top of Quantum Memeology.</p>
        <input type="hidden" id="memeEditId" value="">
        <div class="form-grid">
          <div class="form-group">
            <label>Meme Title</label>
            <input type="text" id="memeTitle" placeholder="e.g., Grover Through the QSVT Lens">
          </div>
          <div class="form-group">
            <label>Category Tag</label>
            <input type="text" id="memeTag" list="memeTagList" placeholder="Select or type category" value="Physics">
            <datalist id="memeTagList">
              <option value="Physics">
              <option value="Quantum Computing">
              <option value="Mathematics & Computer Science">
              <option value="Philosophy & Epistemology">
            </datalist>
          </div>
        </div>

        <div class="form-group">
          <label>Meme Image (Upload from PC or enter path)</label>
          <div style="display:flex; gap:0.75rem; align-items:center;">
            <input type="text" id="memeImage" placeholder="images/my_meme.png" style="flex:1;">
            <label class="btn btn-light" style="cursor:pointer; margin:0;">
              📤 Upload Image File
              <input type="file" accept="image/*" style="display:none;" onchange="uploadFile(this, 'images', 'memeImage')">
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>Short Caption / Punchline Summary</label>
          <input type="text" id="memeDesc" placeholder="Brief one-line setup or punchline shown on the card...">
        </div>

        <div class="form-group">
          <label>💡 Rigorous Technical Explanation ("Why it works")</label>
          <textarea id="memeExp" rows="4" placeholder="Explain the underlying quantum mechanics, pure math theorem, or philosophical argument..."></textarea>
        </div>

        <div style="display:flex; gap:0.6rem;">
          <button class="btn btn-primary" onclick="saveMemeForm()">✓ Save Meme to Portfolio</button>
          <button class="btn btn-light" onclick="resetMemeForm()">Reset Form</button>
        </div>
      </div>

      <div class="card">
        <h2>Manage Existing Memes</h2>
        <p class="card-sub">Click "Edit" to modify any meme, "Top" to feature it first, or "Delete" to remove it.</p>
        <div class="item-list" id="memeListContainer"></div>
      </div>
    </section>

    <!-- 2. BLOG & ESSAYS PANEL -->
    <section class="panel" id="panel-posts">
      <div class="card">
        <h2 id="postFormHeader">✍️ Write / Add Blog Post or Essay</h2>
        <p class="card-sub">Supports Markdown formatting, LaTeX math ($...$ and $$...$$), cover images, and optional external links (e.g., Substack or Bigganblog).</p>
        <input type="hidden" id="postEditSlug" value="">
        <div class="form-grid">
          <div class="form-group">
            <label>Article Title</label>
            <input type="text" id="postTitle" placeholder="e.g., Quantum Contextuality and Epistemic Bounds">
          </div>
          <div class="form-group">
            <label>Category</label>
            <input type="text" id="postCat" list="postCatList" value="Philosophy & Epistemology">
            <datalist id="postCatList">
              <option value="Quantum Computing">
              <option value="Philosophy & Epistemology">
              <option value="Philosophy & Essays">
              <option value="Sociology & Essays">
              <option value="Mathematics & Physics (Bengali)">
            </datalist>
          </div>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label>Publication Date</label>
            <input type="text" id="postDate" placeholder="e.g., October 2026">
          </div>
          <div class="form-group">
            <label>Read Time</label>
            <input type="text" id="postReadTime" placeholder="e.g., 7 min read">
          </div>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label>Cover Image (optional)</label>
            <div style="display:flex; gap:0.5rem;">
              <input type="text" id="postCover" placeholder="images/cover.png">
              <label class="btn btn-light" style="cursor:pointer; margin:0; white-space:nowrap;">
                📤 Upload
                <input type="file" accept="image/*" style="display:none;" onchange="uploadFile(this, 'images', 'postCover')">
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>External Link (optional: Substack / Bigganblog URL)</label>
            <input type="url" id="postExternal" placeholder="https://syedshubha.substack.com/p/...">
          </div>
        </div>
        <div class="form-group">
          <label>Tags (comma-separated)</label>
          <input type="text" id="postTags" placeholder="Quantum Information, Epistemology, Substack">
        </div>
        <div class="form-group">
          <label>Card Summary (1–2 sentences shown on index.html and blog cards)</label>
          <textarea id="postSummary" rows="2" placeholder="Concise overview of the article..."></textarea>
        </div>
        <div class="form-group">
          <label>Full Article Body (Markdown + LaTeX $...$ and $$...$$)</label>
          <textarea id="postContent" rows="10" placeholder="## Introduction&#10;&#10;Write your full essay or technical note here..."></textarea>
        </div>
        <div style="display:flex; gap:0.6rem;">
          <button class="btn btn-primary" onclick="savePostForm()">✓ Save Article to Portfolio</button>
          <button class="btn btn-light" onclick="resetPostForm()">Reset Form</button>
        </div>
      </div>

      <div class="card">
        <h2>Manage Existing Articles & Essays</h2>
        <div class="item-list" id="postListContainer"></div>
      </div>
    </section>

    <!-- 3. PUBLICATIONS PANEL -->
    <section class="panel" id="panel-pubs">
      <div class="card">
        <h2 id="pubFormHeader">📚 Add Accepted / Published Paper</h2>
        <p class="card-sub">Keep your scholarly record strictly restricted to peer-reviewed published/accepted papers.</p>
        <input type="hidden" id="pubEditId" value="">
        <div class="form-grid">
          <div class="form-group">
            <label>Code (e.g., J5 or C8)</label>
            <input type="text" id="pubCode" placeholder="J5">
          </div>
          <div class="form-group">
            <label>Type</label>
            <select id="pubType">
              <option value="journal">Journal Article (journal)</option>
              <option value="conference">Conference Proceeding (conference)</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>Paper Title</label>
          <input type="text" id="pubTitle" placeholder="Full title of the paper">
        </div>
        <div class="form-group">
          <label>Authors (use &lt;strong&gt;S. E. U. Shubha&lt;/strong&gt; to bold your name)</label>
          <input type="text" id="pubAuthors" placeholder="<strong>S. E. U. Shubha</strong>, Coauthor Name, ...">
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label>Venue / Journal</label>
            <input type="text" id="pubVenue" placeholder="e.g., Physical Review A / IEEE QCE">
          </div>
          <div class="form-group">
            <label>Year & Authorship Role</label>
            <div style="display:flex; gap:0.5rem;">
              <input type="text" id="pubYear" placeholder="2026" style="width:110px;">
              <input type="text" id="pubRole" placeholder="1st Author">
            </div>
          </div>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label>DOI / Publisher URL</label>
            <input type="url" id="pubDoi" placeholder="https://doi.org/...">
          </div>
          <div class="form-group">
            <label>PDF File (Upload PDF to assets/files/)</label>
            <div style="display:flex; gap:0.5rem;">
              <input type="text" id="pubPdf" placeholder="assets/files/Paper.pdf">
              <label class="btn btn-light" style="cursor:pointer; margin:0; white-space:nowrap;">
                📤 Upload PDF
                <input type="file" accept=".pdf" style="display:none;" onchange="uploadFile(this, 'files', 'pubPdf')">
              </label>
            </div>
          </div>
        </div>
        <div class="form-group">
          <label>BibTeX Entry</label>
          <textarea id="pubBibtex" rows="4" placeholder="@article{shubha2026,...}"></textarea>
        </div>
        <div style="display:flex; gap:0.6rem;">
          <button class="btn btn-primary" onclick="savePubForm()">✓ Save Publication</button>
          <button class="btn btn-light" onclick="resetPubForm()">Reset</button>
        </div>
      </div>

      <div class="card">
        <h2>Existing Peer-Reviewed Publications</h2>
        <div class="item-list" id="pubListContainer"></div>
      </div>
    </section>

    <!-- 4. NEWS & UPDATES PANEL -->
    <section class="panel" id="panel-updates">
      <div class="card">
        <h2>📢 Add Academic Milestone / News Update</h2>
        <div class="form-grid">
          <div class="form-group">
            <label>Date (e.g., Oct 2026)</label>
            <input type="text" id="updDate" placeholder="Oct 2026">
          </div>
          <div class="form-group">
            <label>Badge (e.g., Paper Accepted, Award, Talk)</label>
            <input type="text" id="updBadge" placeholder="Paper Accepted">
          </div>
        </div>
        <div class="form-group">
          <label>Headline</label>
          <input type="text" id="updTitle" placeholder="Paper Accepted at ...">
        </div>
        <div class="form-group">
          <label>Details (HTML links allowed)</label>
          <textarea id="updContent" rows="3"></textarea>
        </div>
        <button class="btn btn-primary" onclick="addUpdateItem()">✓ Add News Item to Top</button>
      </div>

      <div class="card">
        <h2>Existing News Items</h2>
        <div class="item-list" id="updListContainer"></div>
      </div>
    </section>

    <!-- 5. CV & FILES PANEL -->
    <section class="panel" id="panel-files">
      <div class="card">
        <h2>📄 Update Curriculum Vitae (PDF)</h2>
        <p class="card-sub">Replaces <code>assets/Curriculum_Vitae_Syed_Emad_Uddin_Shubha.pdf</code> across your entire website.</p>
        <label class="dropzone" style="display:block;">
          <strong>📥 Click to Select New CV PDF File</strong>
          <p style="font-size:0.82rem; color:var(--muted); margin-top:0.25rem;">Automatically overwrites Curriculum_Vitae_Syed_Emad_Uddin_Shubha.pdf</p>
          <input type="file" accept=".pdf" style="display:none;" onchange="uploadCV(this)">
        </label>
      </div>

      <div class="card">
        <h2>📁 Upload General PDF / Asset to <code>assets/files/</code></h2>
        <p class="card-sub">Upload slides, accepted camera-ready PDFs, or documents and get a shareable link.</p>
        <label class="dropzone" style="display:block;">
          <strong>📤 Click to Upload File to assets/files/</strong>
          <input type="file" style="display:none;" onchange="uploadFile(this, 'files', 'uploadedFileUrl')">
        </label>
        <div class="form-group" style="margin-top:1rem;">
          <label>Uploaded Relative Path</label>
          <input type="text" id="uploadedFileUrl" readonly placeholder="Path will appear here after upload...">
        </div>
      </div>
    </section>

    <!-- 6. GITHUB SYNC PANEL -->
    <section class="panel" id="panel-git">
      <div class="card">
        <h2>🚀 Publish to GitHub Pages (<code>syedshubha.github.io</code>)</h2>
        <p class="card-sub">Commit all local changes (JSON data, newly uploaded meme images, blog posts, and PDFs) and push directly to the <code>main</code> branch on GitHub.</p>
        <div class="form-group">
          <label>Commit Message</label>
          <input type="text" id="gitCommitMsg" value="Update portfolio content via Portfolio Studio">
        </div>
        <div style="display:flex; gap:0.75rem;">
          <button class="btn btn-gold" onclick="saveAndPushGitHub()">🚀 Save, Commit & Push to GitHub Pages</button>
          <button class="btn btn-light" onclick="checkGitStatus()">🔍 Check Git Status</button>
        </div>
        <pre id="gitLogOutput" style="margin-top:1.25rem; background:#0f172a; color:#e2e8f0; padding:1rem; border-radius:8px; font-family:'JetBrains Mono',monospace; font-size:0.8rem; white-space:pre-wrap; min-height:120px;">Click "Check Git Status" or "Save & Publish to GitHub" to view live output.</pre>
      </div>
    </section>
  </main>
</div>

<div id="statusBanner"></div>

<script>
  let DATA = null;

  function notify(msg, isErr=false) {
    const el = document.getElementById('statusBanner');
    el.style.display = 'block';
    el.style.background = isErr ? '#991b1b' : '#0f172a';
    el.textContent = msg;
    setTimeout(() => { el.style.display = 'none'; }, 4500);
  }

  function switchTab(name, btn) {
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('panel-' + name).classList.add('active');
    btn.classList.add('active');
  }

  async function loadData() {
    const res = await fetch('/api/data');
    DATA = await res.json();
    refreshUI();
  }

  function refreshUI() {
    document.getElementById('countMemes').textContent = (DATA.memes || []).length;
    document.getElementById('countPosts').textContent = (DATA.posts || []).length;
    document.getElementById('countPubs').textContent = (DATA.publications || []).length;
    document.getElementById('countUpdates').textContent = (DATA.updates || []).length;

    // Memes list
    document.getElementById('memeListContainer').innerHTML = (DATA.memes || []).map((m, idx) => `
      <div class="item-row">
        <img src="/${m.image}" class="item-thumb" alt="">
        <div class="item-info">
          <h4>#${idx+1} • ${m.title} <span style="font-size:0.74rem; color:#1d4ed8; font-weight:600;">[${m.tag}]</span></h4>
          <p>${m.desc || ''}</p>
        </div>
        <div class="item-actions">
          <button class="btn btn-light" onclick="moveMemeTop(${idx})" title="Move to Top">⬆️ Top</button>
          <button class="btn btn-light" onclick="editMeme('${m.id}')">✏️ Edit</button>
          <button class="btn btn-danger" onclick="deleteMeme('${m.id}')">✕</button>
        </div>
      </div>
    `).join('');

    // Posts list
    document.getElementById('postListContainer').innerHTML = (DATA.posts || []).map((p, idx) => `
      <div class="item-row" style="${p.hide_from_main ? 'opacity:0.65;' : ''}">
        <div class="item-info">
          <h4>${p.title} <span style="font-size:0.74rem; color:#1d4ed8;">[${p.category}]</span> ${p.hide_from_main ? '<span style="font-size:0.72rem; color:#b91c1c; font-weight:700;">(Hidden from Main Portfolio)</span>' : ''}</h4>
          <p>${p.date || ''} • ${p.external_url || 'Hosted on Portfolio'}</p>
        </div>
        <div class="item-actions">
          <button class="btn btn-light" onclick="toggleHidePost('${p.slug || p.id}')">${p.hide_from_main ? '👁️ Show' : '🙈 Hide'}</button>
          <button class="btn btn-light" onclick="editPost('${p.slug || p.id}')">✏️ Edit</button>
          <button class="btn btn-danger" onclick="deletePost('${p.slug || p.id}')">✕</button>
        </div>
      </div>
    `).join('');

    // Pubs list
    document.getElementById('pubListContainer').innerHTML = (DATA.publications || []).map(p => `
      <div class="item-row">
        <div class="item-info">
          <h4>[${p.code}] ${p.title}</h4>
          <p>${p.venue} (${p.year}) • ${p.role || ''}</p>
        </div>
        <div class="item-actions">
          <button class="btn btn-light" onclick="editPub('${p.id}')">✏️ Edit</button>
          <button class="btn btn-danger" onclick="deletePub('${p.id}')">✕</button>
        </div>
      </div>
    `).join('');

    // Updates list
    document.getElementById('updListContainer').innerHTML = (DATA.updates || []).map((u, idx) => `
      <div class="item-row">
        <div class="item-info">
          <h4>[${u.date}] ${u.title || u.badge}</h4>
          <p>${(u.content || '').replace(/<[^>]+>/g, '')}</p>
        </div>
        <div class="item-actions">
          <button class="btn btn-danger" onclick="deleteUpdate(${idx})">✕</button>
        </div>
      </div>
    `).join('');
  }

  async function uploadFile(inputEl, folder, targetInputId) {
    const file = inputEl.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      const b64 = reader.result.split(',')[1];
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, folder: folder, content_b64: b64 })
      });
      const out = await res.json();
      if (out.ok) {
        document.getElementById(targetInputId).value = out.rel_path;
        notify('✓ Uploaded to ' + out.rel_path);
      } else {
        notify('Upload failed: ' + out.error, true);
      }
    };
    reader.readAsDataURL(file);
  }

  async function uploadCV(inputEl) {
    const file = inputEl.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      const b64 = reader.result.split(',')[1];
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: 'Curriculum_Vitae_Syed_Emad_Uddin_Shubha.pdf', folder: 'cv', content_b64: b64 })
      });
      const out = await res.json();
      if (out.ok) notify('✓ Updated Curriculum_Vitae_Syed_Emad_Uddin_Shubha.pdf!');
      else notify('Failed: ' + out.error, true);
    };
    reader.readAsDataURL(file);
  }

  // MEME CRUD
  function saveMemeForm() {
    const title = document.getElementById('memeTitle').value.trim();
    const tag = document.getElementById('memeTag').value.trim() || 'Quantum Computing';
    const image = document.getElementById('memeImage').value.trim();
    const desc = document.getElementById('memeDesc').value.trim();
    const explanation = document.getElementById('memeExp').value.trim();
    const editId = document.getElementById('memeEditId').value;

    if (!title || !image) { notify('Please provide both a Meme Title and Image.', true); return; }

    if (editId) {
      const idx = DATA.memes.findIndex(m => m.id === editId);
      if (idx >= 0) DATA.memes[idx] = { id: editId, image, title, desc, explanation, tag };
    } else {
      const newId = 'meme-' + Date.now();
      DATA.memes.unshift({ id: newId, image, title, desc, explanation, tag });
    }
    resetMemeForm();
    refreshUI();
    saveDataOnly();
  }

  function editMeme(id) {
    const m = DATA.memes.find(x => x.id === id);
    if (!m) return;
    document.getElementById('memeEditId').value = m.id;
    document.getElementById('memeTitle').value = m.title || '';
    document.getElementById('memeTag').value = m.tag || '';
    document.getElementById('memeImage').value = m.image || '';
    document.getElementById('memeDesc').value = m.desc || '';
    document.getElementById('memeExp').value = m.explanation || '';
    document.getElementById('memeFormHeader').textContent = '✏️ Editing Meme: ' + m.title;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function resetMemeForm() {
    document.getElementById('memeEditId').value = '';
    document.getElementById('memeTitle').value = '';
    document.getElementById('memeImage').value = '';
    document.getElementById('memeDesc').value = '';
    document.getElementById('memeExp').value = '';
    document.getElementById('memeFormHeader').textContent = '➕ Add New Science / Philosophy Meme';
  }

  function moveMemeTop(idx) {
    const item = DATA.memes.splice(idx, 1)[0];
    DATA.memes.unshift(item);
    refreshUI();
    saveDataOnly();
  }

  function deleteMeme(id) {
    if (!confirm('Remove this meme from your portfolio?')) return;
    DATA.memes = DATA.memes.filter(m => m.id !== id);
    refreshUI();
    saveDataOnly();
  }

  // POST CRUD
  function savePostForm() {
    const title = document.getElementById('postTitle').value.trim();
    const category = document.getElementById('postCat').value.trim();
    const date = document.getElementById('postDate').value.trim() || '2026';
    const read_time = document.getElementById('postReadTime').value.trim() || '6 min read';
    const cover_image = document.getElementById('postCover').value.trim();
    const external_url = document.getElementById('postExternal').value.trim();
    const tags = document.getElementById('postTags').value.split(',').map(s => s.trim()).filter(Boolean);
    const summary = document.getElementById('postSummary').value.trim();
    const content = document.getElementById('postContent').value.trim();
    const editSlug = document.getElementById('postEditSlug').value;

    if (!title) { notify('Please enter an Article Title.', true); return; }
    const slug = editSlug || title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    const obj = { id: slug, slug, title, date, category, read_time, tags, external_url, summary, content };
    if (cover_image) obj.cover_image = cover_image;

    if (editSlug) {
      const idx = DATA.posts.findIndex(p => (p.slug || p.id) === editSlug);
      if (idx >= 0) DATA.posts[idx] = obj;
    } else {
      DATA.posts.unshift(obj);
    }
    resetPostForm();
    refreshUI();
    saveDataOnly();
  }

  function editPost(slug) {
    const p = DATA.posts.find(x => (x.slug || x.id) === slug);
    if (!p) return;
    document.getElementById('postEditSlug').value = p.slug || p.id;
    document.getElementById('postTitle').value = p.title || '';
    document.getElementById('postCat').value = p.category || '';
    document.getElementById('postDate').value = p.date || '';
    document.getElementById('postReadTime').value = p.read_time || '';
    document.getElementById('postCover').value = p.cover_image || '';
    document.getElementById('postExternal').value = p.external_url || '';
    document.getElementById('postTags').value = (p.tags || []).join(', ');
    document.getElementById('postSummary').value = p.summary || '';
    document.getElementById('postContent').value = p.content || '';
    document.getElementById('postFormHeader').textContent = '✏️ Editing Article: ' + p.title;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function resetPostForm() {
    document.getElementById('postEditSlug').value = '';
    document.getElementById('postTitle').value = '';
    document.getElementById('postDate').value = '';
    document.getElementById('postReadTime').value = '';
    document.getElementById('postCover').value = '';
    document.getElementById('postExternal').value = '';
    document.getElementById('postTags').value = '';
    document.getElementById('postSummary').value = '';
    document.getElementById('postContent').value = '';
    document.getElementById('postFormHeader').textContent = '✍️ Write / Add Blog Post or Essay';
  }

  function deletePost(slug) {
    if (!confirm('Delete this article?')) return;
    DATA.posts = DATA.posts.filter(p => (p.slug || p.id) !== slug);
    refreshUI();
    saveDataOnly();
  }

  function toggleHidePost(slug) {
    const p = (DATA.posts || []).find(x => (x.slug || x.id) === slug);
    if (!p) return;
    p.hide_from_main = !p.hide_from_main;
    refreshUI();
    saveDataOnly();
  }

  // PUB CRUD
  function savePubForm() {
    const code = document.getElementById('pubCode').value.trim() || 'J';
    const type = document.getElementById('pubType').value;
    const title = document.getElementById('pubTitle').value.trim();
    const authors = document.getElementById('pubAuthors').value.trim();
    const venue = document.getElementById('pubVenue').value.trim();
    const year = document.getElementById('pubYear').value.trim();
    const role = document.getElementById('pubRole').value.trim();
    const doi_url = document.getElementById('pubDoi').value.trim();
    const pdf_url = document.getElementById('pubPdf').value.trim();
    const bibtex = document.getElementById('pubBibtex').value.trim();
    const editId = document.getElementById('pubEditId').value;

    if (!title) { notify('Please provide a Paper Title.', true); return; }
    const id = editId || ('pub-' + Date.now());
    const obj = { id, code, type, title, authors, venue, year, role, doi_url, pdf_url, bibtex };

    if (editId) {
      const idx = DATA.publications.findIndex(p => p.id === editId);
      if (idx >= 0) DATA.publications[idx] = obj;
    } else {
      DATA.publications.unshift(obj);
    }
    resetPubForm();
    refreshUI();
    saveDataOnly();
  }

  function editPub(id) {
    const p = DATA.publications.find(x => x.id === id);
    if (!p) return;
    document.getElementById('pubEditId').value = p.id;
    document.getElementById('pubCode').value = p.code || '';
    document.getElementById('pubType').value = p.type || 'journal';
    document.getElementById('pubTitle').value = p.title || '';
    document.getElementById('pubAuthors').value = p.authors || '';
    document.getElementById('pubVenue').value = p.venue || '';
    document.getElementById('pubYear').value = p.year || '';
    document.getElementById('pubRole').value = p.role || '';
    document.getElementById('pubDoi').value = p.doi_url || '';
    document.getElementById('pubPdf').value = p.pdf_url || '';
    document.getElementById('pubBibtex').value = p.bibtex || '';
    document.getElementById('pubFormHeader').textContent = '✏️ Editing Publication: ' + p.code;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function resetPubForm() {
    document.getElementById('pubEditId').value = '';
    document.getElementById('pubCode').value = '';
    document.getElementById('pubTitle').value = '';
    document.getElementById('pubAuthors').value = '';
    document.getElementById('pubVenue').value = '';
    document.getElementById('pubYear').value = '';
    document.getElementById('pubRole').value = '';
    document.getElementById('pubDoi').value = '';
    document.getElementById('pubPdf').value = '';
    document.getElementById('pubBibtex').value = '';
    document.getElementById('pubFormHeader').textContent = '📚 Add Accepted / Published Paper';
  }

  function deletePub(id) {
    if (!confirm('Remove this publication?')) return;
    DATA.publications = DATA.publications.filter(p => p.id !== id);
    refreshUI();
    saveDataOnly();
  }

  // UPDATES CRUD
  function addUpdateItem() {
    const date = document.getElementById('updDate').value.trim();
    const badge = document.getElementById('updBadge').value.trim();
    const title = document.getElementById('updTitle').value.trim();
    const content = document.getElementById('updContent').value.trim();
    if (!date || !content) { notify('Date and Details are required.', true); return; }
    DATA.updates.unshift({ date, badge, title, content });
    document.getElementById('updDate').value = '';
    document.getElementById('updBadge').value = '';
    document.getElementById('updTitle').value = '';
    document.getElementById('updContent').value = '';
    refreshUI();
    saveDataOnly();
  }

  function deleteUpdate(idx) {
    DATA.updates.splice(idx, 1);
    refreshUI();
    saveDataOnly();
  }

  // SAVE & GIT SYNC
  async function saveDataOnly() {
    const res = await fetch('/api/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(DATA)
    });
    const out = await res.json();
    if (out.ok) notify('💾 Saved to data/portfolio_data.json & portfolio_data.js!');
    else notify('Save error: ' + out.error, true);
  }

  async function saveAndPushGitHub() {
    notify('⏳ Saving & pushing to GitHub Pages...');
    await saveDataOnly();
    const msg = document.getElementById('gitCommitMsg').value.trim() || 'Update portfolio content via Portfolio Studio';
    const res = await fetch('/api/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });
    const out = await res.json();
    document.getElementById('gitLogOutput').textContent = out.log || '';
    if (out.ok) notify('🚀 Published live to https://syedshubha.github.io!');
    else notify('Git push warning: check GitHub Sync tab.', true);
  }

  async function checkGitStatus() {
    const res = await fetch('/api/git_status');
    const out = await res.json();
    document.getElementById('gitLogOutput').textContent = out.log || '';
  }

  loadData();
</script>
</body>
</html>
"""


class StudioHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=REPO_DIR, **kwargs)

    def log_message(self, format, *args):
        pass

    def _send_json(self, obj, status=200):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/studio", "/studio/", "/admin"):
            raw = STUDIO_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/api/data":
            self._send_json(load_portfolio_data())
            return
        if parsed.path == "/api/git_status":
            code, out = run_git_command(["status", "-s"])
            _, branch = run_git_command(["branch", "--show-current"])
            self._send_json({"ok": code == 0, "log": f"Branch: {branch}\n\n{out or 'Working tree clean.'}"})
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, 400)
            return

        if parsed.path == "/api/save":
            try:
                save_portfolio_data(payload)
                self._send_json({"ok": True})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
            return

        if parsed.path == "/api/upload":
            try:
                fname = sanitize_filename(payload.get("filename", "file.bin"))
                folder = payload.get("folder", "images")
                raw_bytes = base64.b64decode(payload.get("content_b64", ""))
                if folder == "cv":
                    os.makedirs(os.path.dirname(CV_PATH), exist_ok=True)
                    dest = CV_PATH
                    rel = "assets/Curriculum_Vitae_Syed_Emad_Uddin_Shubha.pdf"
                elif folder == "files":
                    os.makedirs(FILES_DIR, exist_ok=True)
                    dest = os.path.join(FILES_DIR, fname)
                    rel = f"assets/files/{fname}"
                else:
                    os.makedirs(IMAGES_DIR, exist_ok=True)
                    dest = os.path.join(IMAGES_DIR, fname)
                    rel = f"images/{fname}"
                with open(dest, "wb") as f:
                    f.write(raw_bytes)
                self._send_json({"ok": True, "rel_path": rel})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
            return

        if parsed.path == "/api/publish":
            msg = payload.get("message", "Update portfolio via Portfolio Studio")
            logs = []
            c1, o1 = run_git_command(["add", "-A"])
            logs.append("$ git add -A\n" + o1)
            c2, o2 = run_git_command(["commit", "-m", msg])
            logs.append(f'$ git commit -m "{msg}"\n' + o2)
            c3, o3 = run_git_command(["push", "origin", "main"])
            logs.append("$ git push origin main\n" + o3)
            self._send_json({"ok": c3 == 0, "log": "\n\n".join(logs)})
            return

        self._send_json({"ok": False, "error": "Unknown endpoint"}, 404)


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(FILES_DIR, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), StudioHandler)
    url = f"http://127.0.0.1:{PORT}/studio"
    print("=" * 68)
    print("  Portfolio Studio is running locally!")
    print(f"  -> Studio GUI : {url}")
    print(f"  -> Live Site  : http://127.0.0.1:{PORT}/index.html")
    print("  Press Ctrl+C in this window to stop the server.")
    print("=" * 68)
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Portfolio Studio...")
        server.server_close()


if __name__ == "__main__":
    main()
