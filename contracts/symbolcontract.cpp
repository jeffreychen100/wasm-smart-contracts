#include <eosio/eosio.hpp>
#include <eosio/symbol.hpp>
using namespace eosio;

CONTRACT symbolcontract : public contract {
  public:
    using contract::contract;

    TABLE StoredData {
      uint64_t id;
      eosio::symbol sym;

      uint64_t primary_key() const { return id; }
    };

    using storage_table = eosio::multi_index<"mytable"_n, StoredData>;

    ACTION save( uint64_t id, eosio::symbol sym ) {
      storage_table _storage( get_self(), get_self().value );
      _storage.emplace( get_self(), [&]( auto& row ) {
        row.id = id;
        row.sym = sym;
      });
    }
};