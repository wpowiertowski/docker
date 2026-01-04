#
# .zshrc is sourced in interactive shells.
# It should contain commands to set up aliases,
# functions, options, key bindings, etc.
#

# Load and run completion initialization
autoload -U compinit
compinit -i

# Enable bash completion for select commands
autoload -U bashcompinit
bashcompinit -i

# Keep oodles of command history 
HISTSIZE=1000000
SAVEHIST=1000000
setopt APPEND_HISTORY

# Allow tab completion in the middle of a word.
setopt COMPLETE_IN_WORD

# Set up personal aliases, functions, etc.
# ...(put your own stuff here!)...
setopt PROMPT_SUBST
NEWLINE=$'\n'
PROMPT='%m - %F{light green}%*%f %F{light blue}%~%f %f${NEWLINE}> '
EDITOR=vim

# Key BINDINGS
bindkey "^a" beginning-of-line
bindkey "^e" end-of-line
bindkey "^f" forward-word
bindkey "^b" backward-word
bindkey "\e[3~" delete-char

# colors
export TERM='xterm-256color'

# aliases
alias ll='ls -l'
alias lla='ls -al'
alias s='source '

alias st="git st"
alias lg="git lg"

alias co="code"