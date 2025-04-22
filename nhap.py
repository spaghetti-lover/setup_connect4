class LRUCache {
  public:
    LRUCache(int capacity) {
      this.capacity = capacity;
      this.cahce = OrderedDict()
    }

    def get(self, key: int) -> int:
      if key not in cache:
        return -1
      self.cache.move_to_end(key, last=False)
      return self.cache[key]

    def
}