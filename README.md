# dirquick

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Category](https://img.shields.io/badge/recon-content--discovery-red)

Fast **async web content discovery** (directory/file brute-forcing). Pairs an `aiohttp` worker pool with a wordlist to find hidden paths, with status-code matching, length filtering, extension fuzzing, and a built-in starter wordlist so you can run it with nothing else installed.

## Features
- Async worker pool (tunable concurrency)
- Built-in 70+ entry starter wordlist, or bring your own (`-w`)
- Extension fuzzing (`-x php,bak,txt`)
- Status-code matching (`-m`) and response-length filtering (`--filter-length`)
- Custom headers (`-H 'Authorization: Bearer ...'`)
- Follows nothing by default — reports redirects with their `Location`

## Install
```bash
git clone https://github.com/anvarsadathk/dirquick.git
cd dirquick
pip install -r requirements.txt
python3 dirquick.py --help
```

## Usage
```bash
# Built-in wordlist
python3 dirquick.py https://target.tld/ --yes-authorized

# Custom wordlist + extensions, filter noisy 404-sized bodies
python3 dirquick.py https://target.tld/ -w big.txt -x php,bak \
        --filter-length 1234 --yes-authorized -o hits.txt

# Authenticated discovery
python3 dirquick.py https://target.tld/ -H 'Cookie: session=...' --yes-authorized
```

> dirquick is **active** and noisy — it requires `--yes-authorized` to confirm scope.

## ⚠️ Responsible use
Only brute-force content on hosts you own or are explicitly authorized to test. Respect rate limits and engagement rules.

## License
MIT © Anvar Sadath K.
