#define _GNU_SOURCE
#include "record.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
static uint64_t cases;
static uint32_t le32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static int check(const unsigned char *bytes, size_t count, size_t index) {
    const unsigned char *p = bytes + index * 8;
    const uint32_t raw = (uint32_t)p[0] | ((uint32_t)p[1] << 8);
    const int64_t delta = raw >= 32768 ? (int64_t)raw - 65536 : (int64_t)raw;
    const uint64_t size = (uint32_t)p[2] | ((uint32_t)p[3] << 8);
    RecordView view = {0};
    if (decode_record(bytes, count, index, &view) != 1 ||
        view.address != (uint64_t)(uintptr_t)p || view.delta != delta ||
        view.size != size || view.tag != le32(p + 4)) {
        fprintf(stderr, "decode failed index=%zu raw=%" PRIu32 "\n", index, raw);
        return 0;
    }
    ++cases;
    return 1;
}
static int rejected(const unsigned char *bytes, size_t count, size_t index) {
    RecordView out;
    memset(&out, 0xa5, sizeof out);
    const RecordView before = out;
    return decode_record(bytes, count, index, &out) == 0 &&
           memcmp(&out, &before, sizeof out) == 0;
}
int main(void) {
    unsigned char storage[25] = {0};
    unsigned char *bytes = storage + 1; /* Deliberately unaligned base. */
    for (uint32_t value = 0; value < 65536; ++value) {
        for (size_t i = 0; i < 3; ++i) {
            unsigned char *p = bytes + i * 8;
            const uint32_t size = value ^ UINT32_C(0xffff);
            const uint32_t tag = (value * UINT32_C(65537)) ^ UINT32_C(0xdeadbeef);
            p[0] = (unsigned char)value; p[1] = (unsigned char)(value >> 8);
            p[2] = (unsigned char)size; p[3] = (unsigned char)(size >> 8);
            for (unsigned j = 0; j < 4; ++j) p[4+j] = (unsigned char)(tag >> (8*j));
            unsigned char before[25]; memcpy(before, storage, sizeof before);
            if (!check(bytes, 3, i) || memcmp(before, storage, sizeof before) != 0) return 1;
        }
    }
    if (!rejected(NULL, 3, 0) || !rejected(bytes, 0, 0) ||
        !rejected(bytes, 3, 3) || !rejected(bytes, 3, SIZE_MAX) ||
        decode_record(bytes, 3, 0, NULL) != 0) {
        fputs("rejected call changed output or status\n", stderr); return 1;
    }
    RecordView view = {0};
    if (preserved_registers_ok(bytes, 3, 1, &view) != 1) {
        fputs("callee-saved register contract failed\n", stderr); return 1;
    }
    const long page_value = sysconf(_SC_PAGESIZE);
    if (page_value < 8 || (uintmax_t)page_value > SIZE_MAX / 2) return 1;
    const size_t page = (size_t)page_value;
    unsigned char *region = mmap(NULL, page * 2, PROT_READ | PROT_WRITE,
                                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (region == MAP_FAILED) return 1;
    if (mprotect(region + page, page, PROT_NONE) != 0) return 1;
    unsigned char *last = region + page - 8;
    memcpy(last, bytes, 8);
    if (!check(last, 1, 0) || !rejected(last, 1, 1)) return 1;
    if (munmap(region, page * 2) != 0) return 1;
    printf("record cases=%" PRIu64 " guard=1 abi=6 rejected=5\n", cases);
    return 0;
}
