#ifndef ASSEMBLY_RECORD_H
#define ASSEMBLY_RECORD_H
#include <stddef.h>
#include <stdint.h>
typedef struct {
    uint64_t address;
    int64_t delta;
    uint64_t size;
    uint64_t tag;
} RecordView;
_Static_assert(sizeof(RecordView) == 32, "RecordView layout");
_Static_assert(offsetof(RecordView, delta) == 8, "delta offset");
_Static_assert(offsetof(RecordView, size) == 16, "size offset");
_Static_assert(offsetof(RecordView, tag) == 24, "tag offset");
/* Each readable record is eight bytes: signed LE16 delta, unsigned LE16
   size, unsigned LE32 tag. bytes covers count records; out is a separate
   writable RecordView. Return 0 without reading/writing a record when
   bytes/out is NULL or index >= count. Otherwise fill out and return 1.
   The caller supplies valid storage with count * 8 representable. */
uint64_t decode_record(const unsigned char *bytes, size_t count,
                       size_t index, RecordView *out);
uint64_t preserved_registers_ok(const unsigned char *bytes, size_t count,
                               size_t index, RecordView *out);
#endif
