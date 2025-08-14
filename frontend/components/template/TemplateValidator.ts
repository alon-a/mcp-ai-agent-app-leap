// Template validation and compatibility checking utilities

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  suggestions: string[];
  compatibility: CompatibilityCheck;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
  severity: 'error' | 'warning' | 'info';
}

export interface ValidationWarning {
  field: string;
  message: string;
  code: string;
  suggestion?: string;
}

export interface CompatibilityCheck {
  language: LanguageCompatibility;
  framework: FrameworkCompatibility;
  dependencies: DependencyCompatibility;
  system: SystemCompatibility;
  overall: 'compatible' | 'partial' | 'incompatible';
}

export interface LanguageCompatibility {
  supported: boolean;
  version?: string;
  requiredVersion?: string;
  issues: string[];
}

export interface FrameworkCompatibility {
  supported: boolean;
  version?: string;
  requiredVersion?: string;
  alternatives: string[];
  issues: string[];
}

export interface DependencyCompatibility {
  runtime: DependencyCheck[];
  development: DependencyCheck[];
  system: SystemDependencyCheck[];
  conflicts: string[];
}

export interface DependencyCheck {
  name: string;
  required: string;
  available?: string;
  compatible: boolean;
  issues: string[];
}

export interface SystemDependencyCheck {
  name: string;
  available: boolean;
  version?: string;
  installCommand?: string;
  issues: string[];
}

export interface SystemCompatibility {
  platform: 'windows' | 'macos' | 'linux' | 'unknown';
  architecture: 'x64' | 'arm64' | 'x86' | 'unknown';
  supported: boolean;
  issues: string[];
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: 'built-in' | 'custom' | 'community';
  language: 'python' | 'typescript' | 'go' | 'rust' | 'java' | 'multi';
  framework: string;
  version: string;
  configuration: {
    schema: any;
    defaultValues: Record<string, any>;
    requiredFields: string[];
  };
  dependencies: {
    runtime: Record<string, string>;
    development: Record<string, string>;
    system: string[];
    services: string[];
  };
}

export class TemplateValidator {
  private static instance: TemplateValidator;
  
  public static getInstance(): TemplateValidator {
    if (!TemplateValidator.instance) {
      TemplateValidator.instance = new TemplateValidator();
    }
    return TemplateValidator.instance;
  }

  /**
   * Validate template configuration values
   */
  public validateConfiguration(
    template: Template, 
    values: Record<string, any>
  ): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    const suggestions: string[] = [];

    // Validate required fields
    template.configuration.requiredFields.forEach(field => {
      const value = values[field];
      if (value === undefined || value === null || value === '') {
        errors.push({
          field,
          message: `${field} is required`,
          code: 'REQUIRED_FIELD_MISSING',
          severity: 'error'
        });
      }
    });

    // Validate against JSON schema
    if (template.configuration.schema?.properties) {
      Object.entries(template.configuration.schema.properties).forEach(([field, schema]: [string, any]) => {
        const value = values[field];
        
        if (value !== undefined && value !== null && value !== '') {
          const fieldErrors = this.validateFieldValue(field, value, schema);
          errors.push(...fieldErrors);
        }
      });
    }

    // Template-specific validation
    const templateWarnings = this.validateTemplateSpecific(template, values);
    warnings.push(...templateWarnings);

    // Generate suggestions
    const templateSuggestions = this.generateSuggestions(template, values);
    suggestions.push(...templateSuggestions);

    // Check compatibility
    const compatibility = this.checkCompatibility(template);

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      suggestions,
      compatibility
    };
  }

  /**
   * Validate individual field value against schema
   */
  private validateFieldValue(field: string, value: any, schema: any): ValidationError[] {
    const errors: ValidationError[] = [];

    // Type validation
    switch (schema.type) {
      case 'string':
        if (typeof value !== 'string') {
          errors.push({
            field,
            message: `${field} must be a string`,
            code: 'INVALID_TYPE',
            severity: 'error'
          });
        } else {
          // Pattern validation
          if (schema.pattern) {
            const regex = new RegExp(schema.pattern);
            if (!regex.test(value)) {
              errors.push({
                field,
                message: `${field} format is invalid`,
                code: 'INVALID_PATTERN',
                severity: 'error'
              });
            }
          }

          // Format validation
          if (schema.format) {
            const formatError = this.validateFormat(field, value, schema.format);
            if (formatError) {
              errors.push(formatError);
            }
          }

          // Length validation
          if (schema.minLength && value.length < schema.minLength) {
            errors.push({
              field,
              message: `${field} must be at least ${schema.minLength} characters`,
              code: 'MIN_LENGTH',
              severity: 'error'
            });
          }

          if (schema.maxLength && value.length > schema.maxLength) {
            errors.push({
              field,
              message: `${field} must be at most ${schema.maxLength} characters`,
              code: 'MAX_LENGTH',
              severity: 'error'
            });
          }
        }
        break;

      case 'number':
      case 'integer':
        const numValue = Number(value);
        if (isNaN(numValue)) {
          errors.push({
            field,
            message: `${field} must be a valid number`,
            code: 'INVALID_TYPE',
            severity: 'error'
          });
        } else {
          if (schema.minimum !== undefined && numValue < schema.minimum) {
            errors.push({
              field,
              message: `${field} must be at least ${schema.minimum}`,
              code: 'MIN_VALUE',
              severity: 'error'
            });
          }

          if (schema.maximum !== undefined && numValue > schema.maximum) {
            errors.push({
              field,
              message: `${field} must be at most ${schema.maximum}`,
              code: 'MAX_VALUE',
              severity: 'error'
            });
          }

          if (schema.type === 'integer' && !Number.isInteger(numValue)) {
            errors.push({
              field,
              message: `${field} must be an integer`,
              code: 'INVALID_TYPE',
              severity: 'error'
            });
          }
        }
        break;

      case 'boolean':
        if (typeof value !== 'boolean') {
          errors.push({
            field,
            message: `${field} must be true or false`,
            code: 'INVALID_TYPE',
            severity: 'error'
          });
        }
        break;

      case 'array':
        if (!Array.isArray(value)) {
          errors.push({
            field,
            message: `${field} must be an array`,
            code: 'INVALID_TYPE',
            severity: 'error'
          });
        }
        break;
    }

    // Enum validation
    if (schema.enum && !schema.enum.includes(value)) {
      errors.push({
        field,
        message: `${field} must be one of: ${schema.enum.join(', ')}`,
        code: 'INVALID_ENUM',
        severity: 'error'
      });
    }

    return errors;
  }

  /**
   * Validate format-specific values
   */
  private validateFormat(field: string, value: string, format: string): ValidationError | null {
    switch (format) {
      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
          return {
            field,
            message: `${field} must be a valid email address`,
            code: 'INVALID_EMAIL',
            severity: 'error'
          };
        }
        break;

      case 'uri':
      case 'url':
        try {
          new URL(value);
        } catch {
          return {
            field,
            message: `${field} must be a valid URL`,
            code: 'INVALID_URL',
            severity: 'error'
          };
        }
        break;

      case 'date':
        if (isNaN(Date.parse(value))) {
          return {
            field,
            message: `${field} must be a valid date`,
            code: 'INVALID_DATE',
            severity: 'error'
          };
        }
        break;

      case 'ipv4':
        const ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        if (!ipv4Regex.test(value)) {
          return {
            field,
            message: `${field} must be a valid IPv4 address`,
            code: 'INVALID_IPV4',
            severity: 'error'
          };
        }
        break;
    }

    return null;
  }

  /**
   * Template-specific validation rules
   */
  private validateTemplateSpecific(template: Template, values: Record<string, any>): ValidationWarning[] {
    const warnings: ValidationWarning[] = [];

    // Database template validations
    if (template.id.includes('database')) {
      if (values.database_url) {
        // Check database URL format
        if (!values.database_url.includes('://')) {
          warnings.push({
            field: 'database_url',
            message: 'Database URL should include protocol (e.g., postgresql://)',
            code: 'DATABASE_URL_FORMAT',
            suggestion: 'Use format: protocol://user:password@host:port/database'
          });
        }

        // Recommend connection pooling
        if (!values.pool_size || values.pool_size < 5) {
          warnings.push({
            field: 'pool_size',
            message: 'Consider setting a connection pool size of at least 5 for better performance',
            code: 'CONNECTION_POOL_SIZE',
            suggestion: 'Set pool_size to 10-20 for production use'
          });
        }
      }

      // Security recommendations
      if (!values.ssl_mode || values.ssl_mode === 'disable') {
        warnings.push({
          field: 'ssl_mode',
          message: 'SSL should be enabled for production database connections',
          code: 'SSL_DISABLED',
          suggestion: 'Set ssl_mode to "require" or "verify-full"'
        });
      }
    }

    // API integration template validations
    if (template.id.includes('api')) {
      if (!values.rate_limit || values.rate_limit > 100) {
        warnings.push({
          field: 'rate_limit',
          message: 'Consider implementing rate limiting to prevent API abuse',
          code: 'RATE_LIMIT_HIGH',
          suggestion: 'Set rate_limit to 10-50 requests per second'
        });
      }

      if (!values.timeout || values.timeout > 30000) {
        warnings.push({
          field: 'timeout',
          message: 'Long timeouts may cause poor user experience',
          code: 'TIMEOUT_HIGH',
          suggestion: 'Set timeout to 5000-15000ms for better responsiveness'
        });
      }
    }

    // Web scraper template validations
    if (template.id.includes('scraper')) {
      if (!values.user_agent || values.user_agent.includes('bot')) {
        warnings.push({
          field: 'user_agent',
          message: 'Some websites block requests with bot-like user agents',
          code: 'USER_AGENT_BOT',
          suggestion: 'Use a realistic browser user agent string'
        });
      }

      if (!values.delay || values.delay < 1000) {
        warnings.push({
          field: 'delay',
          message: 'Very short delays between requests may get you blocked',
          code: 'DELAY_TOO_SHORT',
          suggestion: 'Set delay to at least 1000ms between requests'
        });
      }
    }

    // Language-specific validations
    if (template.language === 'python') {
      if (values.python_version && parseFloat(values.python_version) < 3.8) {
        warnings.push({
          field: 'python_version',
          message: 'Python versions below 3.8 are no longer supported',
          code: 'PYTHON_VERSION_OLD',
          suggestion: 'Use Python 3.9 or later for better performance and security'
        });
      }
    }

    if (template.language === 'typescript') {
      if (values.node_version && parseFloat(values.node_version) < 16) {
        warnings.push({
          field: 'node_version',
          message: 'Node.js versions below 16 are no longer in LTS',
          code: 'NODE_VERSION_OLD',
          suggestion: 'Use Node.js 18 LTS or later'
        });
      }
    }

    return warnings;
  }

  /**
   * Generate helpful suggestions based on template and values
   */
  private generateSuggestions(template: Template, values: Record<string, any>): string[] {
    const suggestions: string[] = [];

    // Performance suggestions
    if (template.metadata?.difficulty === 'advanced') {
      suggestions.push('Consider enabling monitoring and logging for production deployments');
    }

    // Security suggestions
    if (template.id.includes('server') || template.id.includes('api')) {
      suggestions.push('Enable HTTPS and implement proper authentication for production use');
    }

    // Language-specific suggestions
    switch (template.language) {
      case 'python':
        suggestions.push('Consider using virtual environments to isolate dependencies');
        if (template.id.includes('database')) {
          suggestions.push('Use connection pooling and async operations for better performance');
        }
        break;

      case 'typescript':
        suggestions.push('Enable strict TypeScript checking for better code quality');
        suggestions.push('Consider using PM2 or similar process manager for production');
        break;

      case 'go':
        suggestions.push('Go binaries are self-contained - no runtime dependencies needed');
        suggestions.push('Consider using Docker for consistent deployment environments');
        break;

      case 'rust':
        suggestions.push('Rust provides memory safety without garbage collection overhead');
        suggestions.push('Consider using cargo-audit to check for security vulnerabilities');
        break;

      case 'java':
        suggestions.push('Configure JVM heap size appropriately for your workload');
        suggestions.push('Consider using GraalVM for faster startup and lower memory usage');
        break;
    }

    // Template-specific suggestions
    if (Object.keys(values).length === 0) {
      suggestions.push('This template works with default settings, but customization is recommended for production use');
    }

    return suggestions;
  }

  /**
   * Check template compatibility with current environment
   */
  private checkCompatibility(template: Template): CompatibilityCheck {
    // This would normally check against actual system capabilities
    // For now, we'll simulate compatibility checking
    
    const languageCompatibility: LanguageCompatibility = {
      supported: true,
      version: this.getLanguageVersion(template.language),
      requiredVersion: this.getRequiredLanguageVersion(template.language),
      issues: []
    };

    const frameworkCompatibility: FrameworkCompatibility = {
      supported: true,
      version: '1.0.0',
      requiredVersion: '1.0.0',
      alternatives: this.getFrameworkAlternatives(template.framework),
      issues: []
    };

    const dependencyCompatibility: DependencyCompatibility = {
      runtime: this.checkRuntimeDependencies(template.dependencies.runtime),
      development: this.checkDevelopmentDependencies(template.dependencies.development),
      system: this.checkSystemDependencies(template.dependencies.system),
      conflicts: []
    };

    const systemCompatibility: SystemCompatibility = {
      platform: this.detectPlatform(),
      architecture: this.detectArchitecture(),
      supported: true,
      issues: []
    };

    // Determine overall compatibility
    let overall: 'compatible' | 'partial' | 'incompatible' = 'compatible';
    
    if (!languageCompatibility.supported || !systemCompatibility.supported) {
      overall = 'incompatible';
    } else if (
      languageCompatibility.issues.length > 0 ||
      frameworkCompatibility.issues.length > 0 ||
      dependencyCompatibility.conflicts.length > 0
    ) {
      overall = 'partial';
    }

    return {
      language: languageCompatibility,
      framework: frameworkCompatibility,
      dependencies: dependencyCompatibility,
      system: systemCompatibility,
      overall
    };
  }

  private getLanguageVersion(language: string): string {
    // Simulate getting installed language version
    const versions: Record<string, string> = {
      python: '3.11.0',
      typescript: '5.0.0',
      go: '1.21.0',
      rust: '1.70.0',
      java: '17.0.0'
    };
    return versions[language] || 'unknown';
  }

  private getRequiredLanguageVersion(language: string): string {
    const requiredVersions: Record<string, string> = {
      python: '3.8.0',
      typescript: '4.5.0',
      go: '1.19.0',
      rust: '1.65.0',
      java: '11.0.0'
    };
    return requiredVersions[language] || '1.0.0';
  }

  private getFrameworkAlternatives(framework: string): string[] {
    const alternatives: Record<string, string[]> = {
      'fastmcp': ['mcp-sdk', 'custom-implementation'],
      'mcp-sdk-ts': ['express-mcp', 'fastify-mcp'],
      'mcp-go': ['gin-mcp', 'echo-mcp'],
      'mcp-rust': ['tokio-mcp', 'actix-mcp'],
      'spring-mcp': ['mcp-java', 'quarkus-mcp']
    };
    return alternatives[framework] || [];
  }

  private checkRuntimeDependencies(dependencies: Record<string, string>): DependencyCheck[] {
    return Object.entries(dependencies).map(([name, required]) => ({
      name,
      required,
      available: required, // Simulate available version
      compatible: true,
      issues: []
    }));
  }

  private checkDevelopmentDependencies(dependencies: Record<string, string>): DependencyCheck[] {
    return Object.entries(dependencies).map(([name, required]) => ({
      name,
      required,
      available: required, // Simulate available version
      compatible: true,
      issues: []
    }));
  }

  private checkSystemDependencies(dependencies: string[]): SystemDependencyCheck[] {
    return dependencies.map(name => ({
      name,
      available: true, // Simulate availability
      version: '1.0.0',
      installCommand: this.getInstallCommand(name),
      issues: []
    }));
  }

  private getInstallCommand(dependency: string): string {
    const commands: Record<string, string> = {
      'postgresql-client': 'apt-get install postgresql-client',
      'redis': 'apt-get install redis-server',
      'chromium': 'apt-get install chromium-browser',
      'docker': 'curl -fsSL https://get.docker.com | sh'
    };
    return commands[dependency] || `# Install ${dependency}`;
  }

  private detectPlatform(): 'windows' | 'macos' | 'linux' | 'unknown' {
    if (typeof navigator !== 'undefined') {
      const platform = navigator.platform.toLowerCase();
      if (platform.includes('win')) return 'windows';
      if (platform.includes('mac')) return 'macos';
      if (platform.includes('linux')) return 'linux';
    }
    return 'unknown';
  }

  private detectArchitecture(): 'x64' | 'arm64' | 'x86' | 'unknown' {
    // This is a simplified detection - in a real implementation,
    // you'd need more sophisticated platform detection
    return 'x64';
  }
}

// Export singleton instance
export const templateValidator = TemplateValidator.getInstance();