# The Zip and Git Tango

This document describes the “Zip & Git Tango” -- a well-choreographed dance for two -- which aims to keep us from stomping on each other’s feet, er, code.

Here's the the whole loop:

1.	Make sure your local project is clean and fully in GitHub
2.	Hand the code to ChatGPT via a zip
3.	ChaptGPT makes changes and hands a zip back
4.	You merge it cleanly into Git and a bug is fixed

##1. Confirm your local project is clean and tracked

From your project root:


```
cd ~/dev/monarch-tools
git status
```

You want to see:

```
On branch main
nothing to commit, working tree clean
```

If you have changes:

```
git add .
git commit -m "WIP before ChatGPT handoff"
```

Check your branch and remote:

```
git branch -vv
git remote -v
```
You want something like:

```
* main   abc1234 [origin/main] Some commit message
origin  https://github.com/jkeiththomson/monarch-tools.git (fetch)
origin  https://github.com/jkeiththomson/monarch-tools.git (push)```
```

If origin isn’t your GitHub repo, fix it:

```
git remote set-url origin https://github.com/jkeiththomson/monarch-tools.git
```

## 2. Push everything to GitHub

Just to be sure your remote is up to date:

```
git push
```

Then in your browser, confirm:

	•	Repo URL: https://github.com/jkeiththomson/monarch-tools
	•	Latest commit matches what you expect
	•	(Optional) Check the Actions tab and see CI running/passing

At this point, your local + remote are in sync and safe.

## 3. Create a clean zip to hand off to ChatGPT

You’ve done this before, but here’s a concrete command that works well and avoids junk:

From your ~/dev directory:

```
cd ~/dev

zip -r monarch-tools-upload.zip monarch-tools \
  -x "monarch-tools/.git/*" \
  -x "monarch-tools/.venv/*" \
  -x "monarch-tools/__pycache__/*" \
  -x "monarch-tools/.pytest_cache/*" \
  -x "monarch-tools/.mypy_cache/*" \
  -x "monarch-tools/.ruff_cache/*"
```

What this does -- Includes everything I need:

* src
* tests
* pyproject.toml
* README.md,
* pre-commit-config.yaml
* github
* etc.

Excludes:

* .git → your Git history stays yours
* .venv → local-only environment
* caches
* Then you upload monarch-tools-upload.zip here in chat and tell me what you want (e.g. “ analyze structure”, “help fix X bug”, “add Y feature”).

⸻

## 4. What I’ll do with your zip (on my side)

When you upload:

* I unzip it into my sandbox (/mnt/data/monarch-tools or similar).
* I:
* inspect the folder structure
* read README.md, pyproject.toml, key modules
* run static analysis / reasoning over the code
* 	make changes if requested (e.g. bug fix, new feature, cleanup)
* 	Then I create a new zip (e.g. monarch-tools-with-fix.zip) that:
* 	does not contain .git or .venv
* 	includes any new/updated files (src/..., tests/..., configs, etc.)
* 	I give you a download link in the chat.

Nothing in this step touches your Git history; it all lives in my sandbox.

⸻

##5. Apply my changes back into your local Git repo

Once you download my zip (say monarch-tools-with-fix.zip) into ~/Downloads:

Make sure your repo is clean:

```
	cd ~/dev/monarch-tools
	git status
```

If you see uncommitted changes
###1. Either Commit them or stash them:


Commit:

	git add .
	git commit -m "Before applying GPT fix"


Stash:

	git stash


### 2. Go up one level and replace / overlay the project:

```
cd ~/dev
```

Option A: unzip over the existing folder (safe: zip has no .git)

```
unzip ~/Downloads/monarch-tools-with-fix.zip
```

If it contains a top-level 'monarch-tools/' folder, it'll overwrite files in place.

Because the zip doesn’t include .git/, your Git history stays untouched, and only tracked files are updated.


#### 3.	Inspect what changed:

```
cd ~/dev/monarch-tools
git status
git diff
```
You should see exactly the modifications I made.

#### 4. If you like the changes, commit them:

```
git add .
git commit -m "Apply GPT changes: <short summary>"
git push```

If something looks wrong, you can always:

```
git reset --hard HEAD
```

and you’re back to the last commit.

### 6. Fixing a bug together – sample workflow

Let’s say you discover a bug in activity:

Example: amounts on refunds are being treated as purchases.

Here’s how we’d loop:

#### Step A — You reproduce it locally

Run the command that shows the bug:

```
monarch-tools activity chase statements/whatever.pdf --debug
```

Note:

* the exact CLI command
* what you expected
* what actually happened
* Optionally, capture a small sample output (a few CSV lines) or traceback.

#### Step B — You hand me the project

Make sure everything is committed & pushed:

```
git add .
git commit -m "Reproduce refund sign bug"
git push
```

Create and upload zip (monarch-tools-upload.zip) as in step 3.

In chat, tell me:
“There’s a bug in refunds in activity.”

Provide the exact command you ran and what was wrong.

#### Step C — I investigate and patch

* I open src/monarch_tools/extractors/chase.py (or relevant file)

* I reason through:

	* Parsing logic
	* Sign handling
	* Special-case refund detection

* I update:
	* the extractor logic
	* maybe add/adjust tests in tests/...

* I re-run my reasoning and prepare a new zip for you (monarch-tools-bugfix.zip).

Step D — You apply and verify

Download my zip and unzip over your project (step 5).


Run:

```
git status
git diff
```
	•	Test the bug again:

```
monarch-tools activity chase statements/whatever.pdf --debug
```

If it looks good:

```
pre-commit run --all-files
git add .
git commit -m "Fix refund sign bug in activity extractor"
git push
```

Now GitHub has the fix, your CI runs it, and it’s part of your official history.

### 7. The “golden rules” of this workflow


#### 1. Always commit before you send me a zip.
- That way, you can always roll back if necessary.

#### 2. Never send .git/ or .venv/ in the zip.

- Keeps zips small and avoids history confusion.

#### 3.	Always inspect git diff after applying my zip.

- You stay in control of what actually changes.

#### 4.	Use one main branch (main) until you’re ready for feature branches.

- Then this same zip workflow still works; you just work on feature/... instead.

⸻
