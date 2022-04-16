;; evaluater.el
;; Author: Arif Er <arifer612@pm.me>
;; Description: Evaluates all source blocks and tangles the file

;; Code:
(require 'org)
(require 'ob-shell)
(require 'ob-python)
(require 'ob-lob)

(setq org-confirm-babel-evaluate 'nil
      org-babel-python-command "python3")

(org-babel-lob-ingest ".github/scripts/babel-scripts.org")
(message "Beginning evaluations.")
(find-file "README.org")
(org-babel-execute-buffer)
(save-buffer)
(message "Evaluation complete!")

;; End of code
