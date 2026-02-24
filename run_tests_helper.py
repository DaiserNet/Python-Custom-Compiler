import unittest

def run():
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_editor.py')
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    with open('fails.txt', 'w') as f:
        f.write(f"Failures: {len(result.failures)}\n")
        for fail in result.failures:
            f.write(str(fail[0]) + "\n" + fail[1] + "\n\n")
        f.write(f"Errors: {len(result.errors)}\n")
        for err in result.errors:
            f.write(str(err[0]) + "\n" + err[1] + "\n\n")

if __name__ == '__main__':
    run()
