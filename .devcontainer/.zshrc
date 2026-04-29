# Enable colors
autoload -U colors && colors

# Enable color support for ls
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# Git prompt integration
autoload -Uz vcs_info
precmd() { vcs_info }
zstyle ':vcs_info:git:*' check-for-changes true
zstyle ':vcs_info:git:*' stagedstr '%F{green}✔%f'
zstyle ':vcs_info:git:*' unstagedstr '%F{red}✗%f'
zstyle ':vcs_info:git:*' formats '%F{yellow}(%b)%f%c%u'
setopt PROMPT_SUBST

# Colorful prompt with Git branch
# PROMPT='%F{green}%n@%m%f:%F{blue}%~%f ${vcs_info_msg_0_}$ '
PROMPT='%F{blue}%~%f ${vcs_info_msg_0_} $ '

# Enable syntax highlighting for common commands (if available)
# Note: zsh-syntax-highlighting package would need to be installed for this
# source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh 2>/dev/null || true

# Enable auto-completion with colors
autoload -U compinit && compinit
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
# Case-insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
# Partial completion (e.g., f-b -> foo-bar)
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'
# Menu selection for completion
zstyle ':completion:*' menu select

# History settings
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt SHARE_HISTORY
setopt HIST_IGNORE_DUPS          # 連続した重複を無視
setopt HIST_IGNORE_ALL_DUPS      # 重複を全て削除
setopt HIST_FIND_NO_DUPS         # 履歴検索で重複を表示しない
setopt HIST_REDUCE_BLANKS        # 余分な空白を削除
setopt HIST_VERIFY               # 履歴展開後、実行前に確認

# History search with arrow keys (現在の入力でフィルタリング)
bindkey "^[[A" history-search-backward
bindkey "^[[B" history-search-forward

# Incremental search with Ctrl+R
bindkey "^R" history-incremental-search-backward

# Directory stack (cd履歴)
setopt AUTO_PUSHD           # cdで自動的にディレクトリスタックに追加
setopt PUSHD_IGNORE_DUPS    # 重複を無視
setopt PUSHD_SILENT         # pushd/popdの出力を抑制
alias d='dirs -v'           # ディレクトリスタック表示

# Typo correction
setopt CORRECT              # コマンドのtypo修正を提案
setopt CORRECT_ALL          # 引数のtypo修正も提案（これは煩わしい場合はコメントアウト）

# Other useful options
setopt AUTO_CD              # ディレクトリ名だけでcd
setopt NO_BEEP              # ビープ音を無効化
setopt INTERACTIVE_COMMENTS # コマンドラインで#以降をコメントとして扱う

# Activate Python virtual environment if it exists
if [ -f /workspace/.venv/bin/activate ]; then
    source /workspace/.venv/bin/activate
fi
