1. create new empty repo
2. clone the remote (the old one) then cd in
3. `git remote rename origin upstream`
4. `git remote add gitea URL_TO_NEW_REPO`
5. `git push gitea main`

To pull patches from the upstream (the old/remote repo):
- `git pull upstream main && git push gitea main`

- commit to a new branch from gitea/main
- make a branch from upstream/main and checkout to it
- `git push <upstream-branch> <gitea-branch>`

