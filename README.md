# recipe-dl

Recipe download script.  Will format the recipe into JSON, Markdown,
or reStructuredText.  I tend to use more reStructuredText so that is the
default output format.

## Usage

```
usage: recipe-dl [-h] [-v] [-a] [-d] [-j] [-m] [-r] [-i INFILE]
                 [-o OUTFILE] [-s]
                 [URL [URL ...]]

positional arguments:
  URL

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -a, --authorize       Force authorization of Cook Illustrated sites
  -d, --debug           Add additional Output
  -v, --verbose         Make output verbose
  -j, --output-json     Output results in JSON format.
  -m, --output-md       Output results in Markdown format.
  -r, --output-rst      Output results in reStructuredText format.
  -i INFILE, --infile INFILE
                        Specify input json file infile.
  -o OUTFILE, --outfile OUTFILE
                        Specify output file outfile.
  -s, --save-to-file    Save output file(s).
  ```

## Compatibility

Currently this has been tested for the following sites:
* [Cook's Illustrated](www.cooksillustrated.com) (Subscription Required)
* [Cook's Country](www.cookscountry.com) (Subscription Required)
* [America's Test Kitchen](www.americatestkitchen.com) (Subscription Required)
* [New York Times](cooking.nytimes.com)
* [Bon Appetit](www.bonappetit.com)
* [FoodNetwork.com](www.foodnetwork.com)
* [CookingChannelTV.com](www.cookingchanneltv.com)

## Install
Install using pip
```sh
pip3 install https://github.com/rodneyshupe/recipe-dl/archive/v0.2.9.tar.gz
```
<!--
Copy recipe-dl.sh to /opt.
```sh
curl https://raw.githubusercontent.com/rodneyshupe/recipe-dl/master/recipe-dl.sh --output /opt/recipe-dl.sh && chmod + x /opt/recipe-dl.sh
curl https://raw.githubusercontent.com/rodneyshupe/recipe-dl/master/rst2recipe.sh --output /opt/recipe-dl.sh && chmod + x /opt/rst2recipe.sh
```

Create symbolic links to somewhere on the path.
```sh
ln -s /opt/rst2recipe.sh /usr/local/bin/rst2recipe
ln -s /opt/rst2recipe.sh /usr/local/bin/rst2recipe
```
-->
