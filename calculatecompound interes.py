P=float(input("ENTER PRINCIPAL AMOUNT:"))
R=float(input("ENTER RATE OF INTEREST:"))
N=float(input("ENTER THE DURATION OF TIME :"))
T=float(input("ENTER COMPUND TIME OF INTEREST:"))
A=P*((1+R//N)**(N*T))
CI=A-P
print("the compound interest is:",CI)
print("the compound interest total amount:",A)