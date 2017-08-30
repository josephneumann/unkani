def validate_addresses(self):
    if self.addresses and isinstance(self.addresses, list):

        existing_addresses = []
        if self.user:
            if self.user.addresses.all():
                for address in self.user.addresses.all():
                    existing_addresses.append(address)

        # Normalize individual addresses
        n_addresses = []
        for addr_dict in self.addresses:
            a_index = n_addresses.index(addr_dict)
            if isinstance(addr_dict, dict):
                address1 = addr_dict.get('address1', None)
                address2 = addr_dict.get('address2', None)
                city = addr_dict.get('city', None)
                state = addr_dict.get('state', None)
                zipcode = addr_dict.get('zipcode', None)
                primary = addr_dict.get('primary', False)
                active = addr_dict.get('active', True)

                aa = AddressAPI(address1=address1, address2=address2, city=city, state=state, zipcode=zipcode,
                                active=active, primary=primary)

                aa.run_validations()
                a, errors = aa.make_object()

                if not a:
                    self.errors['warning']['address{}'.format(
                        a_index)] = 'Unable to create an address from the supplied data.'

                if errors['critical']:
                    for key in errors['critical']:
                        self.errors['warning']['address{}'.format(a_index)][key] = errors['critical'][key]
                if errors['warning']:
                    for key in errors['warning']:
                        self.errors['warning']['address{}'.format(a_index)][key] = errors['warning'][key]

                if isinstance(a, Address):
                    n_addresses.append(a)

        # Look for matching addresses based on address hash.  Update primary and active of existing addresses
        if n_addresses and existing_addresses:
            existing_hashes = {}
            for address in existing_addresses:
                existing_hashes[address.address_hash] = address

            n_addresses_to_drop = []
            for address in n_addresses:
                new_hash = address.generate_address_hash()
                if new_hash in existing_hashes:
                    existing_match = existing_hashes[new_hash]
                    if address.primary and address.active:
                        self.user.swap_primary_address(existing_match)
                    n_addresses_to_drop.append(address)

            for i in n_addresses_to_drop:
                n_addresses.pop(n_addresses.index(i))

        # Handle primary and active flags
        new_primary_cnt = 0
        new_active_count = 0
        if n_addresses:
            # Check for multiple new addresses with primary True
            for a in n_addresses:
                if a.primary:
                    new_primary_cnt += 1
                if a.active:
                    new_active_count += 1
            if new_primary_cnt > 1:
                self.errors['warning'][
                    'addresses'] = 'Multiple primary addresses were supplied.  A user may only have' \
                                   ' on primary address.  The address information was not processed.'
        existing_primary_cnt = 0
        existing_active_cnt = 0
        if existing_addresses:
            for a in existing_addresses:
                if a.primary and a.active:
                    existing_primary_cnt += 1
                    existing_primary = a
                if a.active:
                    existing_active_cnt += 1

        if n_addresses:
            # If a primary is sent, and existing primary, set new as primary
            if new_primary_cnt == 1 and existing_addresses and existing_primary_cnt == 1:
                existing_primary.primary = False

            # If new addresses, and no existing primary address set first new address to primary
            if existing_primary_cnt == 0 and new_primary_cnt == 0:
                n_addresses[0].primary = True

            # If no active new address is supplied
            if new_active_count == 0:
                # If there is no current active address either, raise an error
                if existing_addresses and existing_active_cnt == 0:
                    self.errors['warning']['addresses'] = 'Existing user does not have an active address.  At least' \
                                                          'one new active address must be supplied.'
                    n_addresses = []

                if not existing_addresses:
                    self.errors['warning'][
                        'addresses'] = 'At least one address must be active for the user.  Addresses' \
                                       'could not be set.'
                    n_addresses = []

        self.addresses = n_addresses

    else:
        self.addresses = []