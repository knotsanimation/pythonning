# pythonning

low-level module providing convenient functions and components for working with
python. The intention is that you could share this module with anyone
that have **just python** installed and it will work. Anyone meaning 
a friend, a data-sciencist, a random internet-people.

It is possible some functions have implicit requirements, meaning they except
some software to be on the machine of the user to work. But implicit means
that it doesn't prevent to import the library and use other functions. 

An example would be a function related to git, to get a commit hash. You need
git on your system, but you can still call the function even if you don't have
git installed.

Keep in mind that even if a requirement is implicit for a piece of code,
we might have other better-suited package to store that code.