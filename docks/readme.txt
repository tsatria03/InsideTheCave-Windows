Inside The Cave

Inside The Cave is an audio game: you run through a dark cave in three lanes, and when you hear a monster roar, you move out of its lane.
It was made for the iPhone in 2016, so that blind and sighted players have the same game, and this is its Windows version, playing the original's own sounds.

Headphones

Wear headphones, because you find a monster's lane by where its roar comes from, to your left, ahead of you or to your right.
The game says so itself when it starts.

Starting the game

The game opens on the original's earphone warning, in Portuguese if Windows is in Portuguese, and in English otherwise.
After three seconds it goes on to the main menu, and any key goes on at once.

The main menu

The main menu has three rows: Play, Score and Quit.
Up and Down move between the rows, and your screen reader says each one.
The rows wrap around, so Down on the last row goes back to the first, and Up on the first row goes to the last.
Home and End go to the first and the last row.
Enter or Space chooses the row you are on.
Escape in the main menu quits the game.
Music plays on the main menu, the Score screen and the result screen, and stops when a game starts.

The first three games

On your first three games, a Windows voice says the original's instructions in your language.
Then your screen reader says the keys to move and to throw your torch.
The first monster comes once both are done.
From the fourth game on, the game starts two seconds after you choose Play.

Controls

A or Left Arrow moves you one lane to the left.
D or Right Arrow moves you one lane to the right.
Each move sounds from the lane you move into, and trying to go past the left or right lane bumps into the cave wall on that side.
W or Up Arrow throws your torch up your lane.
P or Escape pauses the game.
Switching away from the game window pauses the game as well.
F1 opens the key bindings.
Home and End make the whole game louder and quieter while you play, in steps of ten percent, and your screen reader says the new master volume.
In a game, Page Up and Page Down make the music louder and quieter, and your screen reader says the new track volume.
On the menus, Page Up and Page Down do the same for the menu music, and your screen reader says the new menu volume.
Alt+F4 quits the game at any moment.

How to play

You stand at the bottom of the middle lane, and monsters come down the lanes toward you.
As a monster comes within reach it roars from its lane, about a second before it reaches you.
Move out of its lane before it gets there.
Bats come down the same way, with a sound of their own, and every seventh thing in your way is bats.
The cave speeds up as you go deeper.
Your footsteps run with you from your lane, a walk at first, then a run after about a minute and a half.

Your torch

Your torch burns down as you go, and its burning sound gets a little quieter as it does.
Your screen reader says Torch low when it starts to dim, and soon after that it goes out, with a sound of its own.
Torches lie on the path, each jingling from its lane as it comes, and running into one gives you a fresh torch.
Throwing your torch kills a monster in your lane, but it uses the torch up, and you score nothing for it.
A bat that your torch hits only dodges into another lane.
You cannot throw a torch that has gone out.

Score and coins

Your score goes up four times a second while you are alive.
Coins come down the lanes too, each dinging from its lane, and each one is ten points.
When you take a coin, you hear it from where you are.

The pause menu

When you pause, the game stops where it is, sounds and all, and a pause menu opens.
It has three rows: Resume, Restart and Quit to menu.
Up and Down move between them, and Enter chooses.
Escape or P resumes the game.
Restart and Quit to menu do not save your score.

Game over

When a monster reaches you, the game ends a second later, and your screen reader says your score and your coins.
Then type your name, up to fifteen characters.
Your screen reader says each character as you type it, and Backspace says the one it removes.
Enter or Down goes on to the Replay row, and the Menu row is below it.
Replay plays again, and Menu or Escape goes back to the main menu.
Both save your score first, if it is in your best five.
A blank name is saved as unnamed player.
A score that is already in your best five is not saved again, so no two of them are the same.

Your best five

Choose Score in the main menu to hear your best five scores, best first, with their names.
Up and Down move through them, and Menu or Escape goes back to the main menu.

Changing the keys

Press F1 to hear every key and change any of them.
Up and Down move through the actions, and Enter changes the key for the one you are on.
A adds a second key, and Delete removes a key.
Press R twice to put every key back as it was.
Escape or F1 goes back.
F1, Escape, Page Up, Page Down, Home and End cannot be changed, so there is always a way out, and the volume keys stay where they are.
The key bindings screen speaks through your screen reader, or through a Windows voice if none is running.

Your save

Your best five scores and how many games have heard the instructions are saved in save.json, your volumes in settings.json, and your keys in keys.json.
All three are in the InsideTheCave folder in your AppData Roaming folder, which you can open by typing %APPDATA%\InsideTheCave into the Windows Run box.
In settings.json you can set three volumes, from 0 for silent to 100 for full volume.
MASTERVOLUME is everything, which Home and End also change during a game.
MUSICVOLUME is the music in a game, the track, which Page Up and Page Down change in a game.
MENUVOLUME is the menu music, which Page Up and Page Down change on the menus.
Change a number in Notepad, save the file and start the game again to hear it.
If save.json or settings.json is ever damaged, the game keeps it with .damaged on the end of its name and carries on from a backup.
If keys.json is damaged, the game uses the usual keys and leaves the file as it is.

Credits

Who made the game, and the licenses, are in credits.txt, beside this file.
