/**
 * uuid7
 * https://gist.github.com/fabiolimace/515a0440e3e40efeb234e12644a6a346
 */
create or replace function uuid7() returns uuid as $$
declare
	v_time timestamp with time zone:= null;
	v_secs bigint := null;
	v_usec bigint := null;

	v_timestamp bigint := null;
	v_timestamp_hex varchar := null;

	v_random bigint := null;
	v_random_hex varchar := null;

	v_bytes bytea;

	c_variant bit(64):= x'8000000000000000'; -- RFC-4122 variant: b'10xx...'
begin

	-- Get seconds and micros
	v_time := clock_timestamp();
	v_secs := EXTRACT(EPOCH FROM v_time);
	v_usec := mod(EXTRACT(MICROSECONDS FROM v_time)::numeric, 10^6::numeric);

	-- Generate timestamp hexadecimal (and set version 7)
	v_timestamp := (((v_secs * 1000) + div(v_usec, 1000))::bigint << 12) | (mod(v_usec, 1000) << 2);
	v_timestamp_hex := lpad(to_hex(v_timestamp), 16, '0');
	v_timestamp_hex := substr(v_timestamp_hex, 2, 12) || '7' || substr(v_timestamp_hex, 14, 3);

	-- Generate the random hexadecimal (and set variant b'10xx')
	v_random := ((random()::numeric * 2^62::numeric)::bigint::bit(64) | c_variant)::bigint;
	v_random_hex := lpad(to_hex(v_random), 16, '0');

	-- Concat timestemp and random hexadecimal
	v_bytes := decode(v_timestamp_hex || v_random_hex, 'hex');

	return encode(v_bytes, 'hex')::uuid;
	
end $$ language plpgsql;

/*alert_enterprise*/
CREATE OR REPLACE FUNCTION public.alert_enterprise()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    VOLATILE
    COST 100
AS $BODY$
BEGIN
	IF ((old.country <> 'Belgique' AND old.country <> new.country) OR 
		(old.zip <> '' AND old.zip <> new.zip) OR
		(old.city <> '' AND old.city <> new.city) OR
		(old.street <> '' AND old.street <> new.street) OR
		(old."number" <> '' AND old."number" <> new."number") OR
		(old.box <> '' and old.box <> new.box) OR
		(old."extraAddressInfo" <> '' AND old."extraAddressInfo" <> new."extraAddressInfo")
	   ) THEN
		INSERT INTO public.companies_alertaddress (id,"enterpriseNumber", created_at)
		VALUES (public.uuid7(), old."enterpriseNumber", CURRENT_TIMESTAMP);
	END IF;
	return new;
END;
$BODY$;

/*alert_establishment*/
CREATE OR REPLACE FUNCTION public.alert_establishment()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    VOLATILE
    COST 100
AS $BODY$
BEGIN
	IF ((old.country <> 'Belgique' AND old.country <> new.country) OR 
		(old.zip <> '' AND old.zip <> new.zip) OR
		(old.city <> '' AND old.city <> new.city) OR
		(old.street <> '' AND old.street <> new.street) OR
		(old."number" <> '' AND old."number" <> new."number") OR
		(old.box <> '' and old.box <> new.box) OR
		(old."extraAddressInfo" <> '' AND old."extraAddressInfo" <> new."extraAddressInfo")
	   ) THEN
		INSERT INTO public.companies_alertaddress (id,"establishmentNumber", created_at)
		VALUES (public.uuid7(), old."establishmentNumber", CURRENT_TIMESTAMP);
	END IF;
	return new;
END;
$BODY$;

/**
* TRIGGER A CREER SUR companies_enterprise
* alert_enterprise_update
* AFTER
* UPDATE
* country, zip, city, street, number, box, extraAddressInfo
*/


/**
* TRIGGER A CREER SUR companiesestablishment
* alert_establishment_update
* AFTER
* UPDATE
* country, zip, city, street, number, box, extraAddressInfo
*/
