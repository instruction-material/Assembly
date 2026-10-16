#include "record.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
int main(int argc, char **argv) {
    if (argc > 2 || (argc == 2 && strcmp(argv[1], "--changed") != 0)) {
        fputs("usage: assembly_demo [--changed]\n", stderr);
        return 64;
    }
    const unsigned char normal[32] = {
        0x00,0x80,0xff,0xff,0x00,0x00,0x00,0x80,
        0xff,0xff,0x00,0x00,0xff,0xff,0xff,0xff,
        0xff,0x7f,0x01,0x00,0x78,0x56,0x34,0x12,
        0x01,0x00,0x00,0x80,0x00,0x00,0x00,0x00
    };
    const unsigned char changed[32] = {
        0xff,0x7f,0x00,0x80,0x01,0x00,0x00,0x00,
        0x00,0x80,0xff,0xff,0xff,0xff,0xff,0xff,
        0x00,0x00,0x01,0x00,0x00,0x00,0x00,0x80,
        0xfe,0xff,0x00,0x00,0x04,0x03,0x02,0x01
    };
    const unsigned char *bytes = argc == 2 ? changed : normal;
    for (size_t i = 0; i < 4; ++i) {
        RecordView view = {0};
        if (decode_record(bytes, 4, i, &view) != 1 ||
            view.address != (uint64_t)(uintptr_t)(bytes + i * 8)) {
            fputs("Record decoder unfinished or incorrect.\n", stderr);
            return 78;
        }
        printf("record=%zu address=0x%" PRIx64 " delta=%" PRId64
               " size=%" PRIu64 " tag=%" PRIu64 "\n",
               i, view.address, view.delta, view.size, view.tag);
    }
    return 0;
}
