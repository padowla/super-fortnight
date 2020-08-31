#!/usr/local/bin/php-cgi -f
<?php
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

