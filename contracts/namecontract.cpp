#include <eosio/eosio.hpp>
using namespace eosio;

CONTRACT namecontract : public contract {
  public:
    using contract::contract;

    TABLE StoredData {
      name id;
      std::string text;
      
      uint64_t primary_key() const { return id.value; }
    };
    
    using storage_table = eosio::multi_index<"mytable"_n, StoredData>;

    ACTION save( name id, std::string text ) {
      storage_table _storage( get_self(), get_self().value );
      _storage.emplace( get_self(), [&]( auto& row ) {
        row.id = id;
        row.text = text;
      });
    }
};