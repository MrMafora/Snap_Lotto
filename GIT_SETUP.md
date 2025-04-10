# Git Repository Setup Instructions

## Setting Up a Remote Repository

To push this repository to GitHub or another Git hosting service, follow these steps:

### GitHub Setup

1. Create a new repository on GitHub named "snap-lotto"
   - Do not initialize it with README, license, or .gitignore files

2. Connect your local repository to the GitHub repository:
   ```
   git remote add origin https://github.com/yourusername/snap-lotto.git
   ```

3. Push your code to GitHub:
   ```
   git push -u origin main
   ```

### GitLab Setup

1. Create a new project on GitLab named "snap-lotto"
   - Do not initialize it with README, license, or .gitignore files

2. Connect your local repository to the GitLab repository:
   ```
   git remote add origin https://gitlab.com/yourusername/snap-lotto.git
   ```

3. Push your code to GitLab:
   ```
   git push -u origin main
   ```

## Working with Branches

For feature development, use feature branches:

```
# Create a new feature branch
git checkout -b feature/new-feature

# Make changes and commit them
git add .
git commit -m "Add new feature"

# Push the feature branch to remote
git push -u origin feature/new-feature
```

## Deployment Workflow

For deployment, consider the following workflow:

1. Develop features in feature branches
2. Merge features to development branch for testing
3. Once tested, merge to main branch for production
4. Tag releases with version numbers:
   ```
   git tag -a v1.0.0 -m "Version 1.0.0"
   git push origin v1.0.0
   ```