# Movie-Extra-Downloader
A python 3.6 script that downloads movie extras from youtube.

This script searches for movie extras on youtube and then uses Youtube-DL to download found videos from youtube. 
Downloaded videos are put into subfolders in the movie directory.

The script uses folder names as a basis of the search. it can also recognise that the folder name ends with the release
year and will use it to make better searches. to improve results the script can use a tmdb api key to filter out
similarly named titles. the script asumes that you are using a folder naming schemes similar to
"{movie title} {movie release year}". it can handle most common delimiters and will remove all parentheses and brackets 

My goal and vision of this program is to find all kind of movie extra content on youtube but for now **I've only implemented 
trailers.** The goal is also to provide options for usefull stuff like renaming schemes. editing the filtering process
should also be fairly easy to mess about with. for now however I woudln't recommend changing to much in the extra configs.

## INFO

it'sa a quite slow script. I've hard coded in a limit of one movie per minute so that you don't get flagged by google.
so expect to run it for a day or two the first time you run it

The provided configs that I've included are well tested but they are **not perfect**. if you find a issue with the script 
finding the wrong movie entirely please let me know.

for now it'll download the video and its thumbnail, name them after the youtube video and move it to a subfolder in the 
movie directory



## Installation

it should be dead simple to install. simply clone the repository and install the python3 modules "youtube-dl" and "google"

if you wish to download 1080p versions then you'll also need to install ffmpeg so that it can be run from the terminal. 
this should be easy in linux but it's a bit messier on Mac or Windows.

## Configuring

you'll need to add a default_config.cfg file into the program folder. there should be a "empty_default_config.cfg".
simply remove the "empty_" from its name and you'll be good to go.

if you have a TMDB API key and wish to use it. open the default_config.cfg file and add it to the tmdb_api_key field. 
this is highly recomended since it will provide a better result! 
getting a tmdb api key is really simple and is completed in under 5 minutes. 

 
there should be a folder called "extra_configs" these are the configs that will be used for each movie. each config in 
this folder represents one extra type. I've included 2 basic configurations: "720p_trailer.cfg" and "_1080p_trailer.cfg".
every config file in this folder will be used to search for extras. which means that if you have multiple trailer configs in 
this folder it will look for multiple trailers. any file startinging with either a '.' or a '\_' will however be ignored.

if you've installed ffmpeg and you wish to download 1080p videos simply remove the '_' in front of the 1080p config and 
add a '\_' in front of the 720p config so that you don't accidentally end up with 2 trailers.

## Running

the program should now be ready to use. run it with python3.5 or 3.6. the program also expects a movie directory
or a movie library. 
giving it a movie directory will only execute the script once on the given directory while giving it a movie library will
run the script on every folder in the given library.

a few exmples on a ubuntu machine:

#### movie directory example:

python 3 Extra-Movie-Downloader -d /media/plex/Movies/Avatar (2009)

#### movie library example:

python3 Extra-Movie-Downloader -l /media/plex/Movies
 



