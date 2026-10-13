#define _GNU_SOURCE
#include "string_routines.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int preserved_strlen_ok(const char *);
int preserved_copy_ok(char *, const char *, uint64_t);
static unsigned cases;
static int check(const char *source, char *dest, uint64_t capacity, size_t available) {
    const size_t length = strlen(source);
    if (length > 64 || available > 80 || capacity > available) abort();
    unsigned char source_before[65], expected[80];
    memcpy(source_before, source, length + 1);
    if (available) memcpy(expected, dest, available);
    if (capacity) {
        const size_t written = length < capacity - 1 ? length : (size_t)capacity - 1;
        memcpy(expected, source, written);
        expected[written] = 0;
    }
    const uint64_t actual_length = asm_strlen_simple(source);
    const uint64_t actual_copy = asm_strlcpy_simple(dest, source, capacity);
    if (actual_length != length || actual_copy != length) {
        fprintf(stderr, "capacity=%" PRIu64 " expected length=%zu actual=%" PRIu64 ",%" PRIu64 "\n",
                capacity, length, actual_length, actual_copy);
        return 0;
    }
    if ((available && memcmp(dest, expected, available)) ||
        memcmp(source, source_before, length + 1)) {
        fputs("copy bytes, terminator or unchanged source contract failed\n", stderr);
        return 0;
    }
    if (!preserved_strlen_ok(source) || !preserved_copy_ok(dest, source, capacity)) {
        fputs("callee-saved register contract failed\n", stderr);
        return 0;
    }
    if ((available && memcmp(dest, expected, available)) ||
        memcmp(source, source_before, length + 1)) {
        fputs("repeated call changed bytes outside the contract\n", stderr);
        return 0;
    }
    ++cases;
    return 1;
}
static int guards(void) {
    const long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) return 0;
    const size_t page = (size_t)page_size;
    const size_t lengths[] = {0, 1, 8, 64};
    for (size_t l = 0; l < 4; ++l) {
        const size_t length = lengths[l];
        const uint64_t capacities[] = {0, 1, 5, length + 1, length + 2};
        for (size_t c = 0; c < 5; ++c) {
            const size_t capacity = (size_t)capacities[c];
            unsigned char *src_map = mmap(NULL, 2 * page, PROT_READ | PROT_WRITE,
                                          MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
            if (src_map == MAP_FAILED) return 0;
            char *source = (char *)(src_map + page - length - 1);
            for (size_t i = 0; i < length; ++i) source[i] = (char)('a' + (int)(i % 26));
            source[length] = 0;
            if (mprotect(src_map + page, page, PROT_NONE) ||
                mprotect(src_map, page, PROT_READ)) { munmap(src_map, 2 * page); return 0; }
            unsigned char *dst_map = mmap(NULL, 2 * page, PROT_READ | PROT_WRITE,
                                          MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
            if (dst_map == MAP_FAILED) { munmap(src_map, 2 * page); return 0; }
            if (mprotect(dst_map + page, page, PROT_NONE)) {
                munmap(src_map, 2 * page); munmap(dst_map, 2 * page); return 0;
            }
            char *dest = (char *)(dst_map + page - capacity);
            if (capacity) memset(dest, 0xa5, capacity);
            const int okay = check(source, dest, capacity, capacity);
            const int src_cleanup = munmap(src_map, 2 * page);
            const int dst_cleanup = munmap(dst_map, 2 * page);
            if (!okay || src_cleanup || dst_cleanup) return 0;
        }
    }
    return 1;
}
int main(void) {
    _Static_assert(sizeof(uint64_t) == sizeof(size_t), "Linux x86-64 size");
    if (!guards()) { fputs("guard-page contract failed\n", stderr); return 1; }
    for (unsigned pattern = 0; pattern < 8; ++pattern) {
        for (size_t length = 0; length <= 64; ++length) {
            unsigned char source[65];
            for (size_t i = 0; i < length; ++i)
                source[i] = (unsigned char)(1 + ((i * 37 + (size_t)pattern * 83) % 255));
            source[length] = 0;
            for (uint64_t capacity = 0; capacity <= 68; ++capacity) {
                unsigned char dest[80];
                memset(dest, 0xa5, sizeof(dest));
                char *pointer = (char *)dest;
                size_t available = sizeof(dest);
                if (!capacity && !(pattern % 2)) { pointer = NULL; available = 0; }
                if (!check((const char *)source, pointer, capacity, available)) return 1;
            }
        }
    }
    printf("%u string cases accepted; bounded writes and unchanged source verified\n", cases);
    return 0;
}
