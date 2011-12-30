import sys

def get_params(file_name):
    params = file_name.split('/')[-1]
    null, alpha, beta, gamma = params.split('_')
    gamma = gamma.replace('.csv', '')
    return alpha, beta, gamma

def grab_numbers(file):
    find_file_name, find_cross_validation, skip_one_line, find_accuracy = 0, 1, 2, 3
    mode = find_file_name
    
    with open(file, 'r') as file:
        for line in file:
            if mode == find_file_name:
                if r'features/2_way' in line:
                    file_name = line[:-1]
                    alpha, beta, gamma = get_params(file_name)
                    mode = find_cross_validation
            elif mode == find_cross_validation:
                if line == '=== Stratified cross-validation ===\n':
                    mode = skip_one_line
            elif mode == skip_one_line:
                mode = find_accuracy
            elif mode == find_accuracy:
                accuracy = line.split()[-2]
                mode = find_file_name
                yield alpha, beta, gamma, accuracy

def write_numbers(in_file, out_file):
    out_file = open(out_file, 'w')
    out_file.write('alpha,beta,gamma,accuracy\n')
    for alpha, beta, gamma, accuracy in grab_numbers(in_file):
        out_file.write(alpha + ',' + beta + ',' + gamma + ',' + accuracy + '\n')
    
def main():
    write_numbers(sys.argv[1], sys.argv[2])

if __name__ == '__main__':
    main()
