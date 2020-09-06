#!/usr/local/bin/php-cgi -f
<?php
/*   
    The /usr/local/etc/php.ini file contains the include_path entry
    which specifies a list of directories, separated by ":", where the functions require(),
    require_once(), include(), fopen() etc ... search for required files. In the case of a
    fresh installation of pfSense, the paths included are:
    include_path = ".:/etc/inc:/usr/local/www:/usr/local/captiveportal:/usr/local/pkg:
                      /usr/local/www/classes:/usr/local/www/classes/Form:/usr/local/share/pear:
                      /usr/local/share/openssl_x509_crl/"
    Inside / etc / inc there are the php filter.inc and config.inc files necessary for the function
    of the script.
*/
#require_once("globals.inc");
require_once("filter.inc");
#require_once("util.inc");
require_once("config.inc"); /* config.inc ==> config.lib.inc */

global $config;

if (count($argv) == 1){
	echo "Pass the interface (ex: wan) please!\n";
	exit;
}

$interface = $argv[1];

/***** 

 Parse /cf/conf/config.xml
 
 From source code https://github.com/pfsense/pfsense/blob/master/src/etc/inc/config.lib.inc:
 config/parse_config
 * NAME
 *   parse_config - Read in config.cache or config.xml if needed and return $config array
 * INPUTS
 *   $parse       - boolean to force parse_config() to read config.xml and generate config.cache
 * RESULT
 *   $config      - array containing all configuration variables

 ******/ 
$config = parse_config(true);
$retval = 42;

function readJSONRules($config, $interface) {
	
	$rules = array();

	for($i=0; $i < count($config[filter][rule]); $i++){

		$rule = $config[filter][rule][$i]; #save single rule to analyze in a local variable
		
		if( strcmp($rule["interface"], $interface) === 0){
			
			$rules[] = $rule; #add rule to array
		}
	}

	global $retval;
        $retval	= 0; #all it's fine
	return json_encode($rules); #return JSON of rules for specified interface

}

echo readJSONRules($config, $interface);

exit($retval);


?>

