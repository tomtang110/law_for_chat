# workflow

## pre-commit
1. install pre-commit

```bash
conda create -n mlserving python=3.8 pre-commit==2.20.* -c conda-forge -y
conda install yapf==0.32.0 pylint==2.15.5 -c conda-forge -y
```

2. `pre-commit install`
3. before `git commit` make sure to run `pre-commit run`

## workflow

1. create a branch for you new feature `git branch -b new-feature`
2. develop your new feature
3. run the `precommit` and `git commit`
4. create a pull request for code review

## vscode integration

1. install the python extension
2. setup you virtual env or conda env
3. choose your own env
4. format code and pylint error prompt (right-click)
