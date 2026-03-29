// Basic frontend tests

const { execSync } = require('child_process');

describe('Frontend Build Tests', () => {
  test('TypeScript compilation', () => {
    try {
      execSync('npx tsc --noEmit', { stdio: 'pipe' });
      expect(true).toBe(true); // If we reach here, compilation succeeded
    } catch (error) {
      fail(`TypeScript compilation failed: ${error.message}`);
    }
  });

  test('ESLint passes', () => {
    try {
      execSync('npm run lint', { stdio: 'pipe' });
      expect(true).toBe(true); // If we reach here, linting passed
    } catch (error) {
      fail(`ESLint failed: ${error.message}`);
    }
  });

  test('Next.js build succeeds', () => {
    try {
      execSync('npm run build', { stdio: 'pipe' });
      expect(true).toBe(true); // If we reach here, build succeeded
    } catch (error) {
      fail(`Next.js build failed: ${error.message}`);
    }
  });
});

describe('Package.json Validation', () => {
  const pkg = require('../package.json');

  test('Package.json has required scripts', () => {
    expect(pkg.scripts).toHaveProperty('dev');
    expect(pkg.scripts).toHaveProperty('build');
    expect(pkg.scripts).toHaveProperty('start');
    expect(pkg.scripts).toHaveProperty('lint');
  });

  test('Package.json has required dependencies', () => {
    expect(pkg.dependencies).toHaveProperty('next');
    expect(pkg.dependencies).toHaveProperty('react');
    expect(pkg.dependencies).toHaveProperty('react-dom');
  });

  test('Package.json has required devDependencies', () => {
    expect(pkg.devDependencies).toHaveProperty('typescript');
    expect(pkg.devDependencies).toHaveProperty('@types/react');
    expect(pkg.devDependencies).toHaveProperty('@types/react-dom');
  });
});

describe('File Structure Tests', () => {
  const fs = require('fs');
  const path = require('path');

  test('Required files exist', () => {
    const requiredFiles = [
      'package.json',
      'next.config.js',
      'tailwind.config.js',
      'Dockerfile'
    ];

    requiredFiles.forEach(file => {
      expect(fs.existsSync(path.join(__dirname, '..', file))).toBe(true);
    });
  });

  test('Required directories exist', () => {
    const requiredDirs = [
      'src',
      'public'
    ];

    requiredDirs.forEach(dir => {
      expect(fs.existsSync(path.join(__dirname, '..', dir))).toBe(true);
    });
  });
});
