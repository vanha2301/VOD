#include <stdio.h>
#include <math.h>

int cau1(int n, int i) {
    if (n < 2) return 0;
    if (i * i > n) return 1;
    if (n % i == 0) return 0;
    return cau1(n, i + 1);
}

int cau2(int n) {
    if (n == 0) return 1;
    return n * cau2(n - 1);
}

int cau3(int n) {
    if (n == 0) return 1;
    return 2 * cau3(n - 1);
}

int cau4(int x, int n) {
    if (n == 0) return 1;
    return x * cau4(x, n - 1);
}

int cau5(int n) {
    if (n < 10) return 1;
    return 1 + cau5(n / 10);
}

int cau6a(int n) {
    if (n == 0) return 0;
    return (2 * n + 1) + cau6a(n - 1);
}

float cau6b(int n) {
    if (n == 0) return 0;
    return (float)n / 2 + cau6b(n - 1);
}

int cau6c(int n) {
    if (n == 0) return 0;
    return cau2(n) + cau6c(n - 1);
}

float cau6d(int n) {
    if (n == 0) return 0;
    return sqrt(n) + cau6d(n - 1);
}

int cau6e(int n) {
    if (n == 1) return 1;
    return cau2(n) * cau6e(n - 1);
}

int main() {
    int n = 5;
    int x = 3;

    if (cau1(n, 2)) printf("La so nguyen to\n");
    else printf("Khong la so nguyen to\n");

    printf("%d\n", cau2(n));
    printf("%d\n", cau3(n));
    printf("%d\n", cau4(x, n));
    printf("%d\n", cau5(12345));

    printf("%d\n", cau6a(n));
    printf("%.2f\n", cau6b(n));
    printf("%d\n", cau6c(n));
    printf("%.2f\n", cau6d(n));
    printf("%d\n", cau6e(3));

    return 0;
}